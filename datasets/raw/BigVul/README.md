# BigVul source datasets

The test and validation datasets are stored as CSV files. The training dataset is stored as the lossless [bigvul_train.csv.gz](bigvul_train.csv.gz) archive so its Git LFS object fits within the 2 GiB per-file upload limit. Compression preserves every byte of the original CSV.

The existing [training manifest](bigvul_train.manifest.json) records the size and SHA-256 of the **uncompressed** training CSV. The reconstructed CSV is ignored by Git; the archive is tracked by Git LFS.

## Restore and verify the training CSV

After downloading the LFS files with `git lfs pull`, run the following Python 3.12 code from the repository root. It restores a missing CSV and verifies it against the existing manifest. An existing CSV is checked without being overwritten.

~~~python
from pathlib import Path
import gzip
import hashlib
import json
import shutil

data = Path("datasets/raw/BigVul")
manifest = json.loads((data / "bigvul_train.manifest.json").read_text())
csv_path = data / manifest["file"]

if not csv_path.exists():
    with gzip.open(data / "bigvul_train.csv.gz", "rb") as source:
        with csv_path.open("xb") as target:
            shutil.copyfileobj(source, target)

with csv_path.open("rb") as source:
    checksum = hashlib.file_digest(source, "sha256").hexdigest()

assert csv_path.stat().st_size == manifest["bytes"], "CSV size mismatch"
assert checksum == manifest["sha256"], "CSV checksum mismatch"
print("Verified the original BigVul training CSV.")
~~~

## Original upstream download instructions

To download the testing dataset used for evaluation in our experiments, run the following commands:
```
gdown https://drive.google.com/uc?id=1h0iFJbc5DGXCXXvvR6dru_Dms_b2zW4V
```

To download the training and evaluation dataset used for evaluation in our experiments, run the following commands:
```
gdown https://drive.google.com/uc?id=1ldXyFvHG41VMrm260cK_JEPYqeb6e6Yw
gdown https://drive.google.com/uc?id=1yggncqivMcP0tzbh8-8Eu02Edwcs44WZ
```

To download the whole (i.e., train+val+test) unsplit dataset dataset, run the following commands:
```
gdown https://drive.google.com/uc?id=10-kjbsA806Zdk54Ax8J3WvLKGTzN8CMX
```  
