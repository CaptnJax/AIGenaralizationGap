"""Run in Colab before evaluation to add a batch progress bar to LineVul."""
from pathlib import Path

path = Path("/content/LineVul/linevul/linevul_main.py")
if not path.is_file():
    raise FileNotFoundError("Run the LineVul repository download cell first.")

source = path.read_text(encoding="utf-8")
old = "    for batch in test_dataloader:"
new = (
    "    for batch in tqdm(test_dataloader, total=len(test_dataloader), "
    'desc="LineVul inference", unit="batch", mininterval=2.0, '
    "dynamic_ncols=True):"
)

if new in source:
    print("Batch progress bar is already installed.")
else:
    if source.count(old) != 1 or "from tqdm import tqdm" not in source:
        raise RuntimeError("Unexpected LineVul source layout; no changes made.")
    patched = source.replace(old, new, 1)
    compile(patched, str(path), "exec")
    backup = path.with_name("linevul_main.before_progress.py")
    if not backup.exists():
        backup.write_bytes(path.read_bytes())
    path.write_text(patched, encoding="utf-8")
    print("Installed batch counter, elapsed time, processing rate and ETA.")
    print("Original source backup:", backup)
