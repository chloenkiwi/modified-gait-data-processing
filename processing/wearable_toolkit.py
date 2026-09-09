"""
wearalbe_toolkit.py

@Author: Dianxin

This package is used to preprocess data collected from walking trials.
Read Visual3D, Sage IMU, and compatible optical CSV exports.
Synchronize vicon data and sage data.

"""
import csv
import warnings
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt
import matplotlib.pyplot as plt
from scipy import linalg
from const import SENSOR_LIST, IMU_FIELDS, FORCE_DATA_FIELDS, COHORT
import wearable_math

class Visual3dCsvReader:
    """
    read v3d export data. It should contain LEFT_KNEE_MOMENT,LEFT_KNEE_ANGLE etc.
    """
    v3d_columns = ['Frame'] + [x + y + z for x in ['RIGHT_', 'LEFT_'] for y in ['HIP_ANGLE', 'HIP_MOMENT', 'KNEE_ANGLE', 'KNEE_MOMENT', 'ANKLE_ANGLE', 'ANKLE_MOMENT'] for z in ['_X', '_Y', '_Z']]
    ik_columns = [x + y + z for x in ['RIGHT_', 'LEFT_'] for y in ['HIP_ANGLE', 'KNEE_ANGLE', 'ANKLE_ANGLE'] for z in ['_X', '_Y', '_Z']]
    id_columns = [x + y + z for x in ['RIGHT_', 'LEFT_'] for y in ['HIP_MOMENT', 'KNEE_MOMENT', 'ANKLE_MOMENT'] for z in ['_X', '_Y', '_Z']]

    def __init__(self, file_path):
        self.data = pd.read_csv(file_path, delimiter='\t', header=1, skiprows=[2, 3, 4], encoding_errors='ignore', on_bad_lines='warn')
        self.data.columns = self.v3d_columns
        self.data.fillna(0)
        self.data_frame_ik = self.data[self.ik_columns]
        self.data_frame_id = self.data[self.id_columns]

    def new_headers(self):
        self.data_frame_ik.columns = [col + ' (deg)' for col in self.data_frame_ik.columns]
        self.data_frame_id.columns = [col + ' (Nm/kg)' for col in self.data_frame_id.columns]

    def crop(self, start_index):
        self.data = self.data.loc[start_index:]
        self.data.index = range(self.data.shape[0])
        self.data_frame_ik = self.data_frame_ik.loc[start_index:]
        self.data_frame_ik.index = range(self.data_frame_ik.shape[0])
        self.data_frame_id = self.data_frame_id.loc[start_index:]
        self.data_frame_id.index = range(self.data_frame_id.shape[0])

    def reset_index(self, start_index):
        self.data.index = range(start_index, start_index + self.data.shape[0])
        self.data.index = self.data.index / 100.0
        self.data_frame_ik.index = range(start_index, start_index + self.data_frame_ik.shape[0])
        self.data_frame_ik.index = self.data_frame_ik.index / 100.0
        self.data_frame_id.index = range(start_index, start_index + self.data_frame_id.shape[0])
        self.data_frame_id.index = self.data_frame_id.index / 100.0
[PARENT_TITLE, SAMPLE_RATE, TITLE, DIRECTION, UNITS, DATA] = range(6)

class ViconCsvReader:
    """
    Read the csv files exported from vicon.
    The csv file should only contain Trajectories information
    """

    def __init__(self, file_path, segment_definitions=None, static_trial=None, sub_info=None):
        (self.data, self.sample_rate) = ViconCsvReader.reading(file_path)
        self.segment_data = dict()
        if segment_definitions is None:
            segment_definitions = {}
        for (segment, markers) in segment_definitions.items():
            self.segment_data[segment] = pd.Series(dict([(marker, self.data[marker]) for marker in markers]))
        if static_trial is not None:
            (calibrate_data, _) = ViconCsvReader.reading(static_trial)
            for (segment, markers) in segment_definitions.items():
                segment_data = pd.Series(dict([(marker, calibrate_data[marker]) for marker in markers]))
                self.fill_missing_marker(segment_data, self.segment_data[segment])
        if COHORT == 'overground':
            force_names_japan = ['Imported Kistler Force Plate (Internal Amplifier) #' + plate_num + ' - ' + data_type for plate_num in ['1', '2', '3', '4'] for data_type in ['Force', 'Moment', 'CoP']]
            if force_names_japan[0] in self.data.keys():
                used_force_names = force_names_japan
            else:
                warnings.warn('Force data not found in the csv file.')
                used_force_names = []
            force_array = np.concatenate([self.data[force_name] for force_name in used_force_names], axis=1)
            filtered_force_df = pd.DataFrame(force_array, columns=FORCE_DATA_FIELDS)
        else:
            force_names_ori = ['Imported Bertec Force Plate #' + plate_num + ' - ' + data_type for plate_num in ['1', '2'] for data_type in ['Force', 'Moment', 'CoP']]
            force_names_possible = ['Bertec Force Plate #' + plate_num + ' - ' + data_type for plate_num in ['1', '2'] for data_type in ['Force', 'Moment', 'CoP']]
            force_names_possible_2 = ['Plate ' + plate_num + ' - ' + data_type for plate_num in ['1', '2'] for data_type in ['Force', 'Moment', 'CoP']]
            if force_names_ori[0] in self.data.keys():
                used_force_names = force_names_ori
            elif force_names_possible[0] in self.data.keys():
                used_force_names = force_names_possible
            elif force_names_possible_2[0] in self.data.keys():
                used_force_names = force_names_possible_2
            else:
                warnings.warn('Force data not found in the csv file.')
                used_force_names = []
            if used_force_names:
                force_array = np.concatenate([self.data[force_name] for force_name in used_force_names], axis=1)
                filtered_force_df = pd.DataFrame(force_array, columns=FORCE_DATA_FIELDS)
            else:
                filtered_force_df = pd.DataFrame(columns=FORCE_DATA_FIELDS)
        self.force_df = filtered_force_df
        self.segment_definitions = segment_definitions
        if segment_definitions != {}:
            markers = [marker for markers in segment_definitions.values() for marker in markers]
            self.data_frame = pd.concat([self.data[marker] for marker in markers], axis=1)
            self.data_frame.columns = [marker + '_' + axis for marker in markers for axis in ['X', 'Y', 'Z']]

    def new_headers(self, sixth_hospital=False, Kyoto=False):
        for col in self.data_frame.columns:
            self.data_frame.rename(columns={col: col + ' (mm)'}, inplace=True)
        if COHORT == 'overground':
            for col in self.force_df.columns:
                if sixth_hospital or Kyoto:
                    if 'plate_1' in col:
                        self.force_df.rename(columns={col: col.replace('plate_1', 'plate_lf')}, inplace=True)
                    elif 'plate_2' in col:
                        self.force_df.rename(columns={col: col.replace('plate_2', 'plate_rt')}, inplace=True)
                    elif 'plate_3' in col:
                        self.force_df.rename(columns={col: col.replace('plate_3', 'plate_lf1')}, inplace=True)
                    elif 'plate_4' in col:
                        self.force_df.rename(columns={col: col.replace('plate_4', 'plate_rt1')}, inplace=True)
                elif 'plate_1' in col:
                    self.force_df.rename(columns={col: col.replace('plate_1', 'plate_rt')}, inplace=True)
                elif 'plate_2' in col:
                    self.force_df.rename(columns={col: col.replace('plate_2', 'plate_lf')}, inplace=True)
                elif 'plate_3' in col:
                    self.force_df.rename(columns={col: col.replace('plate_3', 'plate_rt1')}, inplace=True)
                elif 'plate_4' in col:
                    self.force_df.rename(columns={col: col.replace('plate_4', 'plate_lf1')}, inplace=True)
        else:
            for col in self.force_df.columns:
                if sixth_hospital:
                    if 'plate_1' in col:
                        self.force_df.rename(columns={col: col.replace('plate_1', 'plate_lf')}, inplace=True)
                    elif 'plate_2' in col:
                        self.force_df.rename(columns={col: col.replace('plate_2', 'plate_rt')}, inplace=True)
                elif 'plate_1' in col:
                    self.force_df.rename(columns={col: col.replace('plate_1', 'plate_rt')}, inplace=True)
                elif 'plate_2' in col:
                    self.force_df.rename(columns={col: col.replace('plate_2', 'plate_lf')}, inplace=True)
        for col in self.force_df.columns:
            if 'force' in col:
                self.force_df.rename(columns={col: col + ' (N)'}, inplace=True)
            elif 'cop' in col:
                self.force_df.rename(columns={col: col + ' (mm)'}, inplace=True)
            elif 'moment' in col:
                self.force_df.rename(columns={col: col + ' (N*mm)'}, inplace=True)

    @staticmethod
    def reading(file_path):
        data_collection = dict()
        sample_rate_collection = {}
        state = PARENT_TITLE
        with open(file_path, encoding='utf-8-sig') as f:
            for row in csv.reader(f):
                if state == PARENT_TITLE:
                    parent_title = row[0]
                    state = SAMPLE_RATE
                elif state == SAMPLE_RATE:
                    sample_rate_collection[parent_title] = float(row[0])
                    state = TITLE
                elif state == TITLE:
                    titles = list()
                    for col in row[2:]:
                        if col != '':
                            if 'Trajectories' == parent_title:
                                (_, title) = col.split(':')
                            else:
                                title = col
                        titles.append(title)
                    state = DIRECTION
                elif state == DIRECTION:
                    directions = [i for i in row[2:]]
                    data = [[] for _ in directions]
                    state = UNITS
                elif state == UNITS:
                    state = DATA
                elif state == DATA:
                    if row == []:
                        state = PARENT_TITLE
                        for title in titles:
                            data_collection[title] = dict()
                        for (i, direction) in enumerate(directions):
                            data_collection[titles[i]][direction] = data[i]
                        for (key, value) in data_collection.items():
                            data_collection[key] = pd.DataFrame(value)
                        continue
                    for (i, x) in enumerate(row[2:]):
                        try:
                            data[i].append(float(x))
                        except ValueError:
                            data[i].append(np.nan)
        return (data_collection, sample_rate_collection)

    def get_angular_velocity_theta(self, segment, check_len):
        segment_data_series = self.segment_data[segment]
        sampling_rate = 100.0
        walking_data = pd.concat(segment_data_series.tolist(), axis=1).values
        check_len = min(walking_data.shape[0], check_len)
        marker_number = int(walking_data.shape[1] / 3)
        angular_velocity_theta = np.zeros([check_len])
        next_marker_matrix = walking_data[0, :].reshape([marker_number, 3])
        for i_frame in range(check_len):
            if i_frame == 0:
                continue
            current_marker_matrix = next_marker_matrix
            next_marker_matrix = walking_data[i_frame, :].reshape([marker_number, 3])
            (R_one_sample, _) = rigid_transform_3d(current_marker_matrix, next_marker_matrix)
            theta = np.math.acos((np.matrix.trace(R_one_sample) - 1) / 2)
            angular_velocity_theta[i_frame] = theta * sampling_rate / np.pi * 180
        return angular_velocity_theta

    def crop(self, start_index, end_index=None):
        self.data_frame = self.data_frame.loc[start_index:end_index]
        self.data_frame.index = range(self.data_frame.shape[0])
        self.force_df = self.force_df.loc[start_index * 10:end_index * 10 if end_index is not None else None]
        self.force_df.index = range(self.force_df.shape[0])
        for (segment, markers) in self.segment_definitions.items():
            for marker in markers:
                self.segment_data[segment][marker] = self.segment_data[segment][marker].loc[start_index:end_index]
                self.segment_data[segment][marker].index = range(self.segment_data[segment][marker].shape[0])

    def reset_index(self, start_index):
        self.data_frame.index = range(start_index, start_index + self.data_frame.shape[0])
        self.data_frame.index = self.data_frame.index / 100.0
        self.force_df.index = range(start_index * 10, start_index * 10 + self.force_df.shape[0])
        self.force_df.index = self.force_df.index / 1000.0
        for (segment, markers) in self.segment_definitions.items():
            for marker in markers:
                self.segment_data[segment][marker].index = range(start_index, start_index + self.segment_data[segment][marker].shape[0])
                self.segment_data[segment][marker].index = self.segment_data[segment][marker].index / 100.0

    def find_tpose(self, verbose=True):
        start = 0
        end = 0
        marker_data = self.data_frame.copy()
        marker_data_diff = marker_data.diff()[1:]
        marker_data_diff_norm = np.linalg.norm(marker_data_diff, axis=1)
        if verbose:
            plt.plot(marker_data_diff_norm)
            plt.title('Norm of marker data diff -- find T-pose time')
            plt.show()
        mask = marker_data_diff_norm < 5.0
        indices = np.where(mask)[0]
        segments = np.split(indices, np.where(np.diff(indices) != 1)[0] + 1)
        valid_segments = [seg for seg in segments if len(seg) > 200]
        sig = False
        try:
            temp_indices = np.where(marker_data_diff_norm > 40.0)[0]
            temp_index = temp_indices[0]
            temp_end_index = temp_indices[-1]
            for i in range(len(valid_segments)):
                if valid_segments[i][0] > temp_index and valid_segments[i][-1] < temp_end_index:
                    if len(valid_segments[i]) > 400:
                        middle = (valid_segments[i][0] + valid_segments[i][-1]) // 2
                        start = middle - 200
                        end = middle + 200
                        print(f'Start: {start}, End: {end}, Duration: 4 seconds')
                        sig = True
                    elif len(valid_segments[i]) > 200:
                        middle = (valid_segments[i][0] + valid_segments[i][-1]) // 2
                        start = middle - 100
                        end = middle + 100
                        print(f'Start: {start}, End: {end}, Duration: 2 seconds')
                        sig = True
            if not sig:
                print('No valid segment found.')
        except IndexError as e:
            print('No valid segment found.')
            raise
        return (int(start), int(end))

    def fill_missing_marker(self, calibrate_makers, motion_markers):
        if sum([motion_marker.isnull().sum().sum() for motion_marker in motion_markers.tolist()]) == 0:
            return
        calibrate_makers = pd.concat(calibrate_makers.tolist(), axis=1).values
        calibrate_makers = calibrate_makers[0, :].reshape([-1, 3])
        walking_data = pd.concat(motion_markers.tolist(), axis=1).values
        data_len = walking_data.shape[0]
        for i_frame in range(data_len):
            marker_matrix = walking_data[i_frame, :].reshape([-1, 3])
            coordinate_points = np.argwhere(~np.isnan(marker_matrix[:, 0])).reshape(-1)
            missing_points = np.argwhere(np.isnan(marker_matrix[:, 0])).reshape(-1)
            if len(missing_points) == 0:
                continue
            if len(coordinate_points) >= 3:
                (origin, x, y, z) = wearable_math.generate_coordinate(calibrate_makers[coordinate_points, :])
                (origin_m, x_m, y_m, z_m) = wearable_math.generate_coordinate(marker_matrix[coordinate_points, :])
                for missing_point in missing_points.tolist():
                    relative_point = wearable_math.get_relative_position(origin, x, y, z, calibrate_makers[missing_point, :])
                    missing_data = wearable_math.get_world_position(origin_m, x_m, y_m, z_m, relative_point)
                    motion_markers[missing_point]['X'][i_frame] = missing_data[0]
                    motion_markers[missing_point]['Y'][i_frame] = missing_data[1]
                    motion_markers[missing_point]['Z'][i_frame] = missing_data[2]
        for motion_marker in motion_markers:
            motion_marker.interpolate(method='linear', axis=0, inplace=True)

class SageCsvReader:
    """
    Read the csv file exported from sage systems
    """

    def __init__(self, file_path):
        self.data = pd.read_excel(file_path, sheet_name='Sheet1')
        self.sample_rate = 100
        self.data_frame = self.data[[field + '_' + str(index + 1) for index in range(len(SENSOR_LIST)) for field in IMU_FIELDS]].copy()
        for i in range(1, len(self.data['Package_1'])):
            if self.data['Package_1'].iloc[i] < self.data['Package_1'].iloc[i - 1]:
                self.data.loc[i:, 'Package_1'] += 65536
        index = self.data['Package_1'] - self.data['Package_1'].iloc[0]
        if index.size - 1 != index.iloc[-1]:
            print(f'Inconsistent shape, {index.size - 1} samples but last index is {index.iloc[-1]}')
        self.data_frame.index = index
        self.data_frame = self.data_frame.reindex(range(0, int(index.iloc[-1] + 1)))
        self.data_frame.columns = ['_'.join([col.split('_')[0], SENSOR_LIST[int(col.split('_')[1]) - 1]]) for col in self.data_frame.columns]
        self.data_frame = self.data_frame.interpolate(method='linear', axis=0)

    def new_headers(self, mag_calib):
        acc_units = 'm/s^2'
        gyro_units = 'deg/s'
        mag_units = 'uT'
        for col in self.data_frame.columns:
            if 'Accel' in col:
                self.data_frame.rename(columns={col: col + ' (' + acc_units + ')'}, inplace=True)
            elif 'Gyro' in col:
                self.data_frame.rename(columns={col: col + ' (' + gyro_units + ')'}, inplace=True)
            elif 'Mag' in col:
                if not mag_calib:
                    self.data_frame.rename(columns={col: col + ' (' + mag_units + ')'}, inplace=True)

    def get_norm(self, sensor, field, is_plot=False):
        assert sensor in SENSOR_LIST
        assert field in ['Accel', 'Gyro']
        norm_array = np.linalg.norm(self.data_frame[[field + direct + '_' + sensor for direct in ['X', 'Y', 'Z']]], axis=1)
        if is_plot:
            plt.figure()
            plt.plot(norm_array)
            plt.show()
        return norm_array

    def crop(self, start_index):
        self.data = self.data.loc[start_index:]
        self.data.index = self.data.index - self.data.index[0]
        self.data_frame = self.data_frame.loc[start_index:]
        self.data_frame.index = self.data_frame.index - self.data_frame.index[0]

    def reset_index(self, start_index):
        self.data.index = range(start_index, start_index + self.data.shape[0])
        self.data.index = self.data.index / 100.0
        self.data_frame.index = range(start_index, start_index + self.data_frame.shape[0])
        self.data_frame.index = self.data_frame.index / 100.0

    def remove_gyro_offset(self, imu_static_path):
        if imu_static_path.endswith('.csv'):
            imu_static = pd.read_csv(imu_static_path)
        else:
            imu_static = pd.read_excel(imu_static_path)
        FIELD_LIST = ['GyroX_', 'GyroY_', 'GyroZ_']
        drift_list = []
        title = []
        sensor_num = 8
        for sensor in SENSOR_LIST:
            for field in FIELD_LIST:
                title.append(f'{field}{sensor}')
        for i in range(1, sensor_num + 1):
            gyro_cols = [f'GyroX_{i}', f'GyroY_{i}', f'GyroZ_{i}']
            x = imu_static[gyro_cols].to_numpy()
            drift = np.mean(x, axis=0)
            drift_list.extend(drift)
        drift_df = pd.DataFrame([drift_list], columns=title)
        common_cols = drift_df.columns
        self.data_frame[common_cols] = self.data_frame[common_cols] - drift_df[common_cols].values
        print('Gyro offset removed')

def data_filter(data, cut_off_fre, sampling_fre, filter_order=4):
    fre = cut_off_fre / (sampling_fre / 2)
    (b, a) = butter(filter_order, fre, 'lowpass')
    if len(data.shape) == 1:
        data_filtered = filtfilt(b, a, data)
    else:
        data_filtered = filtfilt(b, a, data, axis=0)
    return data_filtered

def rigid_transform_3d(a, b):
    """
    Get the Rotation Matrix and Translation array between A and B.
    return:
        R: Rotation Matrix, 3*3
        T: Translation Array, 1*3
    """
    assert len(a) == len(b)
    N = a.shape[0]
    centroid_A = np.mean(a, axis=0)
    centroid_B = np.mean(b, axis=0)
    AA = a - np.tile(centroid_A, (N, 1))
    BB = b - np.tile(centroid_B, (N, 1))
    H = np.dot(AA.T, BB)
    (U, _, V_t) = linalg.svd(np.nan_to_num(H))
    R = np.dot(V_t.T, U.T)
    if np.linalg.det(R) < 0:
        V_t[2, :] *= -1
        R = np.dot(V_t.T, U.T)
    T = -np.dot(R, centroid_A.T) + centroid_B.T
    return (R, T)

def sync_via_correlation(data1, data2, verbose=False):
    data1 = data_filter(data1, 15, 100, 2)
    data2 = data_filter(data2, 15, 100, 2)
    correlation = np.correlate(data1, data2, 'full')
    delay = len(data2) - np.argmax(correlation) - 1
    if verbose:
        plt.figure()
        if delay > 0:
            plt.plot(data1)
            plt.plot(data2[delay:])
        else:
            plt.plot(data1[-delay:])
            plt.plot(data2)
            plt.legend(['vicon', 'imu'])
        plt.show()
    return delay
