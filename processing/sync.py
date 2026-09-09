"""One configurable synchronization/export entry point for all three sites."""
import argparse
import os
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=int, choices=[1, 2, 3], required=True)
    parser.add_argument('--raw-root', type=Path, required=True)
    parser.add_argument('--output-root', type=Path, required=True)
    parser.add_argument('--subject', required=True, help='Raw metadata key, supplied locally')
    parser.add_argument('--output-id', required=True)
    parser.add_argument('--trials', nargs='+', required=True, help='Explicit trial names/prefixes')
    parser.add_argument('--mode', choices=['indoor', 'outdoor'], default='indoor')
    parser.add_argument('--sheet', help='Override raw metadata worksheet')
    return parser.parse_args()


def trial_records(folder, trials):
    for trial in trials:
        # Preserve legacy acquisition-directory order and repeat suffixes.
        matches = [f[:-4] for f in os.listdir(folder) if f.startswith(trial)]
        for i, name in enumerate(matches):
            yield name, trial if i == 0 else trial + str(i)


def save_frame(frame, destination, start, stop, rate):
    import numpy as np
    data = frame.loc[start:stop, :].copy()
    data.index = np.arange(len(data)) / rate
    data.to_csv(destination, index_label='Time (s)')


def export_events(source, destination, optical_delay, tpose_duration, start_time):
    import numpy as np
    import pandas as pd
    events = pd.read_csv(source, header=None, sep='\t', skiprows=5,
                         encoding_errors='ignore').loc[:, 1:]
    events.columns = ['R_heelstrike (s)', 'R_toeoff (s)', 'L_heelstrike (s)', 'L_toeoff (s)']
    events = events - optical_delay / 100.0 - tpose_duration
    events = events[(events['R_heelstrike (s)'] > start_time) &
                    (events['L_heelstrike (s)'] > start_time)]
    if len(events) < 2:
        raise ValueError('Fewer than two event rows remain; inspect the raw events.')
    for side in ['R', 'L']:
        off, strike = f'{side}_toeoff (s)', f'{side}_heelstrike (s)'
        if events[off].iloc[0] < events[strike].iloc[0] < events[off].iloc[1]:
            events[off] = np.append(events[off].iloc[1:].values, np.nan)
    events.dropna().to_csv(destination, index=False)


def process(args, toolkit, segments):
    import pandas as pd
    overground = args.site == 3
    raw = args.raw_root / args.subject
    output = args.output_root / args.output_id
    if output.exists():
        raise FileExistsError('Use a new output location; existing participant output is protected.')
    if args.output_root.resolve() == args.raw_root.resolve():
        raise ValueError('Raw and output roots must differ.')
    calibrated = (raw / 'imu_mag_calibrated').exists()

    def read_imu(name, allow_csv_static=True):
        path = raw / ('imu_mag_calibrated' if calibrated else 'imu') / (name + ('_calibrated.xlsx' if calibrated else '.xlsx'))
        if not path.exists():
            return None
        imu = toolkit.SageCsvReader(str(path))
        static = raw / 'imu/IMU_static.xlsx'
        if allow_csv_static and not static.exists():
            static = raw / 'imu/IMU_static.csv'
        imu.remove_gyro_offset(str(static))
        return imu

    if args.mode == 'outdoor':
        for name in args.trials:
            if not (raw / 'imu' / (name + '.xlsx')).exists():
                continue
            imu = read_imu(name, allow_csv_static=False)
            if imu is None:
                raise FileNotFoundError('Calibrated input missing: ' + name)
            imu.new_headers(calibrated)
            folder = output / name
            folder.mkdir(parents=True, exist_ok=True)

            data = imu.data_frame.copy()
            data.index = (
                data.index.to_numpy(dtype=float) - float(data.index[0])
            ) / float(imu.sample_rate)
            data.to_csv(folder / 'imu.csv', index_label='Time (s)')
        return

    sheet = args.sheet if args.sheet is not None else 0
    metadata = pd.read_excel(args.raw_root / 'subject_info.xlsx', sheet_name=sheet)
    selected = metadata[metadata['Subject Name'] == args.subject]
    if len(selected) != 1:
        raise ValueError('Raw metadata must contain exactly one matching Subject Name.')
    info = selected.iloc[0]
    for name, export_name in trial_records(raw / 'vicon', args.trials):
        optical = toolkit.ViconCsvReader(str(raw / 'vicon' / (name + '.csv')), segments, None, info)
        imu = read_imu(name)
        if overground and imu is None:
            raise FileNotFoundError('Overground indoor IMU input missing: ' + name)
        tpose_start, tpose_stop = (0, 0) if overground else optical.find_tpose()
        initial = -tpose_start
        minimum = initial
        lag = None
        if imu is not None:
            optical_norm = optical.get_angular_velocity_theta('R_SHANK', 3000)
            imu_norm = imu.get_norm('R_SHANK', 'Gyro')[:3000]
            lag = toolkit.sync_via_correlation(optical_norm, imu_norm, True)
            minimum = min(initial, lag)
            imu.crop(lag - minimum)
        optical_delay = -minimum
        optical.crop(optical_delay)
        v3d_path = str(raw / 'v3d' / (name + '.csv'))
        v3d = toolkit.Visual3dCsvReader(v3d_path)
        v3d.crop(optical_delay)
        optical.reset_index(0)
        v3d.reset_index(0)
        if overground:
            optical.new_headers(False, True)
        else:
            optical.new_headers(args.site == 2)
        v3d.new_headers()
        frames = {'marker.csv': optical.data_frame, 'ik.csv': v3d.data_frame_ik}
        if imu is not None:
            imu.reset_index(0)
            imu.new_headers(calibrated)
            frames['imu.csv'] = imu.data_frame
        duration = (tpose_stop - tpose_start) / 100.0
        stop = (min(len(frame) for frame in frames.values()) - 1) / 100.0
        tpose_dir, trial_dir = output / export_name / 'Tpose', output / export_name / 'Trial'
        tpose_dir.mkdir(parents=True, exist_ok=True)
        trial_dir.mkdir(parents=True, exist_ok=True)
        for filename, frame in frames.items():
            frame.loc[:duration, :].to_csv(tpose_dir / filename, index_label='Time (s)')
            save_frame(frame, trial_dir / filename, duration, stop, 100.0)
        save_frame(v3d.data_frame_id, trial_dir / 'id.csv', duration, stop, 100.0)
        if not optical.force_df.empty:
            # Retain the original exported force time base; not a new resampler.
            save_frame(optical.force_df, trial_dir / 'fp.csv', duration, stop, 1000.0)
        skip_events = name in ['squat', 'sit2stand'] or (not overground and imu is not None and optical.force_df.empty)
        if not skip_events:
            start_time = imu.data_frame.index[0] if imu is not None else optical.data_frame.index[0]
            export_events(raw / 'gait event' / (name + '_gait_event.txt'),
                          trial_dir / 'gait_event.csv', optical_delay, duration, start_time)
        print(f'{export_name}: optical crop={optical_delay}, IMU lag={lag}, T-pose={duration:g} s')


def main():
    args = parse_args()
    os.environ['GAIT_COHORT'] = 'overground' if args.site == 3 else 'treadmill'
    # Configure once before importing shared readers; one site per process.
    import wearable_toolkit
    from const import SEGMENT_DEFINITIONS
    process(args, wearable_toolkit, SEGMENT_DEFINITIONS)


if __name__ == '__main__':
    main()
