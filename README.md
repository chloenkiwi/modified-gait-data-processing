# Modified gait dataset: core processing code

One configurable Python pipeline, shared readers, MATLAB magnetometer calibration,
and site-specific Visual3D templates. No raw recordings, participant metadata,
personal calibration results, or commercial software are included.

## Usage

Install `requirements.txt` in a dedicated environment, then run:

```powershell
python processing/sync.py --site 1 --raw-root C:/data/raw --output-root C:/data/new-output --subject RAW_KEY --output-id OUTPUT_KEY --trials baseline walk_speed_small walk_speed_large
```

Use site 1/2 for treadmill recordings and site 3 for overground-cohort recordings.
Run one site per process. Subject keys and output IDs are supplied locally, never
built into the code. Trial selection is explicit because original scripts contained
temporary task selections, not complete task inventories. For IMU-only recordings
use `--mode outdoor --trials overground stair`. Existing output participant folders
are protected against overwrite. Inspect synchronization diagnostic plots.

Expected inputs under `raw/RAW_KEY/`: `imu/` (trial spreadsheets and IMU_static),
optional `imu_mag_calibrated/`, `vicon/` (compatible optical CSV exports), `v3d/`,
and `gait event/` (trial-specific text exports). `raw/subject_info.xlsx` uses
`Sheet1` for sites 1/2 and `Subjects` for site 3; override with `--sheet`.
Indoor processing matches the raw `Subject Name` field and requires the other
reader-specific fields, including treadmill plate calibration offsets. This raw
schema differs from the public metadata schema. The legacy `vicon` path is an
input-format convention, not a claim that every recording used Vicon.

## Shared implementation

`processing/sync.py` is the sole entry point. `wearable_toolkit.py`, `const.py`,
and `wearable_math.py` contain shared readers and required mathematical helpers.
Only Python functions reachable from the synchronization workflow are retained;
unrelated gait-parameter extraction, orientation estimation, and scaling utilities
have been removed. MATLAB and Visual3D are independent preprocessing steps.

| Behavior | Sites 1/2 | Site 3 |
| --- | --- | --- |
| T-pose | Detected interval | One initial frame |
| Optical/IMU sync windows | 4000/3200 samples | 3000/3000 samples |
| Force plates | Two with metadata COP offsets | Four |
| Trial discovery | Exact name | Prefix plus legacy repeat suffix |
| Optical/V3D rate handling | Original treadmill logic | Original downsampling logic |

Marker definitions, plate labeling, and packet-reset handling remain cohort
branches, not two duplicate pipelines. Shared reader branch ASTs were compared
against the prior source copies. Export orchestration has been refactored; added
safeguards reject existing output folders, ambiguous metadata, and insufficient
gait-event rows. Full numerical equivalence on raw recordings is not established.

## MATLAB and Visual3D

MATLAB scripts are under `processing/matlab`. Set `GAIT_RAW_ROOT` and `GAIT_SUBJECT`
in MATLAB, add this directory to the path, and work in a new writable directory.
Run `one_dynamic_magcal_cal_offset` or `magcal_cal_offset`, then `magcal_process`.
The latter reads the generated calibration MAT file and writes spreadsheets into
the raw input tree: use a working copy. MATLAB with `magcal` support is required.

Visual3D configurations are under `processing/visual3d/site1`, `site2`, and `site3`.
Site 1 uses `dataset_model_NEW.mdh`; site 3 uses `model.mdh`; both expect
`Calib_<task>*.c3d`. Site 2 includes `model_builder.v3s`; its processing pipeline
expects a built `model.mdh` in the selected data folder.

Replace every `REPLACE_WITH_MEASURED_VALUE` with measured mass (kg) or height (m)
before execution. Review paths, trial lists, and remaining template geometry for
the new recording. Placeholders are deliberately non-numeric, not runnable
defaults. Site 3's supplied pipeline selects baseline only. These snapshots do
not reconstruct all original manual adjustments. MATLAB/Visual3D execution has
not been tested during this preparation.

## Scope and checks

Full processing requires raw inputs not distributed here. Later release curation
(ID mapping, sample/package-to-time conversion, invalid magnetometer replacement,
and empty-trial removal) is not implemented here. IMU-only export retains its
legacy package index; it is not the final release time column. Force export retains
the original 1000-Hz time assignment; review before using other acquisition rates.
Released-data examples and manuscript validation scripts are separate resources.

Dependencies are inferred from imports, not historical pinned versions. Syntax,
structural, and synthetic checks do not substitute for full raw-data validation.
The repository does not distribute a tests directory.
`provenance.json` identifies the original Python source groups and hashes; its
file labels describe pre-refactor source inputs rather than the current layout.
Confirm original authorship and redistribution rights before assigning a blanket
open-source license. No new license or unverified software version/DOI is asserted.
