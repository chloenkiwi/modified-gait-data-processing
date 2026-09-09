# Modified gait dataset: core processing code

Python synchronization/export, MATLAB magnetometer calibration, and Visual3D
workflows. Raw recordings and participant metadata are not included.

## Python

Install `requirements.txt`, then run:

```powershell
python processing/sync.py --site 1 --raw-root C:/data/raw --output-root C:/data/output --subject RAW_KEY --output-id OUTPUT_KEY --trials baseline walk_speed_small walk_speed_large
```

- Sites 1/2: treadmill cohort; site 3: overground cohort.
- Use a new output folder and inspect synchronization diagnostic plots.

Inputs: `raw/subject_info.xlsx` and `raw/RAW_KEY/{imu, vicon, v3d, gait event}/`,
with optional `imu_mag_calibrated/`. Metadata defaults to the first worksheet;
use `--sheet NAME` to select another. `RAW_KEY` must match `Subject Name`.
The legacy `vicon` folder name denotes a compatible export format, not a required
motion-capture manufacturer.

## MATLAB and Visual3D

For `processing/matlab`, set `GAIT_RAW_ROOT` and `GAIT_SUBJECT` in MATLAB.
Run `one_dynamic_magcal_cal_offset` or `magcal_cal_offset`, then `magcal_process`.
Use a working copy: calibrated spreadsheets are written into the input tree.
MATLAB with `magcal` support is required.

Visual3D files are in `processing/visual3d/site1`, `site2`, and `site3`.
Sites 1/3 use `model.mdh` and `Calib_<task>*.c3d`; site 2 includes
`model_builder.v3s`. Configure paths, trial lists, and measured mass/height
(`REPLACE_WITH_MEASURED_VALUE`) before running with licensed Visual3D.

Full reprocessing requires the original inputs and manual processing decisions.
These scripts do not reproduce subsequent dataset-release curation automatically.
