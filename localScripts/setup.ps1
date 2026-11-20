param(
    [ValidateSet('cuda', 'cpu')][string]$Compute = 'cuda',
    [string]$Python = ''
)
$ErrorActionPreference = 'Stop'
$envDir = Join-Path $PSScriptRoot '.venv'
$envPython = Join-Path $envDir 'Scripts\python.exe'

if (-not (Test-Path -LiteralPath $envPython)) {
    if ($Python) {
        $launcher = $Python
        $launcherArgs = @()
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        $launcher = 'py'
        $launcherArgs = @('-3.12')
    } else {
        throw 'Install Python 3.12 (64-bit) from python.org, or supply -Python C:\path\to\python.exe.'
    }
    & $launcher @launcherArgs -c "import sys; assert sys.version_info[:2] == (3, 12), 'Use Python 3.12 for this environment.'"
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 is unavailable. Install it from python.org or use -Python with its executable path.' }
    & $launcher @launcherArgs -m venv $envDir
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the local virtual environment.' }
}
& $envPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip setup failed.' }
$wheelIndex = if ($Compute -eq 'cuda') { 'https://download.pytorch.org/whl/cu128' } else { 'https://download.pytorch.org/whl/cpu' }
# Force selection of the requested build even when changing an existing environment.
& $envPython -m pip install --upgrade --force-reinstall 'torch==2.7.1' --index-url $wheelIndex
if ($LASTEXITCODE -ne 0) { throw 'PyTorch installation failed.' }
& $envPython -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& $envPython -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Installed packages have incompatible dependencies.' }
& $envPython -m pip freeze | Set-Content -LiteralPath (Join-Path $envDir 'installed-packages.txt') -Encoding utf8
& $envPython -c "import torch; from clang import cindex; cindex.Index.create(); print('PyTorch:', torch.__version__); print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none'); print('Clang: available')"
if ($LASTEXITCODE -ne 0) { throw 'Dependency smoke check failed.' }
if ($Compute -eq 'cuda') {
    & $envPython -c "import torch; assert torch.cuda.is_available(), 'CUDA requested but unavailable: check the NVIDIA driver, or rerun setup.ps1 -Compute cpu.'"
    if ($LASTEXITCODE -ne 0) { throw 'CUDA verification failed.' }
}
Write-Host 'Setup complete. No datasets or models have been evaluated.'
Write-Host "Start with: & '$envPython' '$PSScriptRoot\pivd_local.py' --jobs sanity"
