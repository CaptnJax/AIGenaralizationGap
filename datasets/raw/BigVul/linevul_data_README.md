# BigVul download provenance for RQ

The public repository includes the official test and validation CSVs and a
lossless training archive. Follow the [BigVul guide](README.md) to obtain the
LFS objects, restore the training CSV, and locate the control reproduction steps.

The upstream LineVul release used these source downloads:

| Split | Upstream source | Public-copy filename |
| --- | --- | --- |
| Test | [Google Drive source](https://drive.google.com/uc?id=1h0iFJbc5DGXCXXvvR6dru_Dms_b2zW4V) | `bigvul_test.csv` |
| Train | [Google Drive source](https://drive.google.com/uc?id=1ldXyFvHG41VMrm260cK_JEPYqeb6e6Yw) | `bigvul_train.csv.gz` restores `bigvul_train.csv` |
| Validation | [Google Drive source](https://drive.google.com/uc?id=1yggncqivMcP0tzbh8-8Eu02Edwcs44WZ) | `bigvul_valid.csv` |

These links document provenance. For the recorded RQ comparison, use the supplied
versions and their manifests rather than substituting a different split or resampling.
