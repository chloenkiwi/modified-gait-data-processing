import os
COHORT = os.environ.get('GAIT_COHORT', 'treadmill')
if COHORT not in ('treadmill', 'walkway'):
    raise ValueError('Invalid GAIT_COHORT')
if COHORT == 'walkway':
    SEGMENT_DEFINITIONS = {'L_FOOT': ['LFCC', 'LFM5', 'LFM2', 'LFMT'], 'R_FOOT': ['RFCC', 'RFM5', 'RFM2', 'RFMT'], 'L_SHANK': ['LTAM', 'LFAL', 'LSHK_CLST_1', 'LSHK_CLST_2', 'LSHK_CLST_3'], 'R_SHANK': ['RTAM', 'RFAL', 'RSHK_CLST_1', 'RSHK_CLST_2', 'RSHK_CLST_3'], 'L_THIGH': ['LFME', 'LFLE', 'LFT', 'LTH_CLST_1', 'LTH_CLST_2', 'LTH_CLST_3'], 'R_THIGH': ['RFME', 'RFLE', 'RFT', 'RTH_CLST_1', 'RTH_CLST_2', 'RTH_CLST_3'], 'WAIST': ['LIPS', 'RIPS', 'LIAS', 'RIAS'], 'CHEST': ['MAI', 'SXS', 'SJN', 'CV7', 'LAC', 'RAC']}
else:
    SEGMENT_DEFINITIONS = {'L_FOOT': ['LFCC', 'LFM5', 'LFM2', 'LFMT', 'LFOOT_IMU_1', 'LFOOT_IMU_2', 'LFOOT_IMU_3'], 'R_FOOT': ['RFCC', 'RFM5', 'RFM2', 'RFMT', 'RFOOT_IMU_1', 'RFOOT_IMU_2', 'RFOOT_IMU_3'], 'L_SHANK': ['LTAM', 'LFAL', 'LSHK_CLST_1', 'LSHK_CLST_2', 'LSHK_CLST_3', 'LSHK_IMU_1', 'LSHK_IMU_2', 'LSHK_IMU_3'], 'R_SHANK': ['RTAM', 'RFAL', 'RSHK_CLST_1', 'RSHK_CLST_2', 'RSHK_CLST_3', 'RSHK_IMU_1', 'RSHK_IMU_2', 'RSHK_IMU_3'], 'L_THIGH': ['LFME', 'LFLE', 'LFT', 'LTH_CLST_1', 'LTH_CLST_2', 'LTH_CLST_3', 'LTH_IMU_1', 'LTH_IMU_2', 'LTH_IMU_3'], 'R_THIGH': ['RFME', 'RFLE', 'RFT', 'RTH_CLST_1', 'RTH_CLST_2', 'RTH_CLST_3', 'RTH_IMU_1', 'RTH_IMU_2', 'RTH_IMU_3'], 'WAIST': ['LIPS', 'RIPS', 'LIAS', 'RIAS', 'PEL_IMU_1', 'PEL_IMU_L', 'PEL_IMU_R'], 'CHEST': ['MAI', 'SXS', 'SJN', 'CV7', 'LAC', 'RAC', 'THO_IMU_1', 'THO_IMU_2', 'THO_IMU_3']}
SENSOR_LIST = ['L_FOOT', 'R_FOOT', 'L_SHANK', 'R_SHANK', 'L_THIGH', 'R_THIGH', 'PELVIS', 'CHEST']
IMU_FIELDS = ['AccelX', 'AccelY', 'AccelZ', 'GyroX', 'GyroY', 'GyroZ', 'MagX', 'MagY', 'MagZ']
if COHORT == 'walkway':
    FORCE_DATA_FIELDS = ['plate_' + num + '_' + data_type + '_' + axis for num in ['1', '2', '3', '4'] for data_type in ['force', 'moment', 'cop'] for axis in ['x', 'y', 'z']]
else:
    FORCE_DATA_FIELDS = ['plate_' + num + '_' + data_type + '_' + axis for num in ['1', '2'] for data_type in ['force', 'moment', 'cop'] for axis in ['x', 'y', 'z']]
