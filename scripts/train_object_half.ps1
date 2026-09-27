$ErrorActionPreference = "Stop"
$project = Split-Path -Parent $PSScriptRoot
Set-Location $project

$env:PYTHONUTF8 = "1"
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONPATH = Join-Path $project "compat"
$env:MPLCONFIGDIR = Join-Path $project ".mpl-cache"
$env:LOCALAPPDATA = Join-Path $project ".localappdata"
$env:TORCH_HOME = Join-Path $project ".torch-cache"

& (Join-Path $project ".train-venv\Scripts\ns-train.exe") splatfacto `
    --output-dir (Join-Path $project "outputs\checkpoints\object-half") `
    --experiment-name dragon-object-half `
    --max-num-iterations 30000 `
    --vis tensorboard `
    --steps-per-save 5000 `
    --steps-per-eval-all-images 5000 `
    --pipeline.model.background-color white `
    colmap `
    --data (Join-Path $project "data\nerfstudio\dragon") `
    --downscale-factor 2 `
    --masks-path masks `
    --eval-mode interval `
    --eval-interval 14
