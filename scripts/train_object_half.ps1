param(
    [string]$Data = (Join-Path $PSScriptRoot "../data/nerfstudio/dragon"),
    [string]$Output = (Join-Path $PSScriptRoot "../outputs/checkpoints/object-half"),
    [string]$NsTrain = "ns-train"
)
$ErrorActionPreference = "Stop"
foreach ($relative in @("images", "images_2", "masks", "masks_2", "colmap/sparse/0")) {
    if (-not (Test-Path -LiteralPath (Join-Path $Data $relative))) {
        throw "Missing prepared data: $relative. Run prepare_nerfstudio_data.py first."
    }
}
if (-not (Get-Command $NsTrain -ErrorAction SilentlyContinue)) {
    throw "ns-train not found. Activate the Nerfstudio environment or pass -NsTrain."
}
& $NsTrain splatfacto `
    --output-dir $Output `
    --experiment-name dragon-object-half `
    --max-num-iterations 30000 `
    --vis tensorboard `
    --steps-per-save 5000 `
    --steps-per-eval-all-images 5000 `
    --pipeline.model.background-color white `
    colmap `
    --data $Data `
    --downscale-factor 2 `
    --masks-path masks `
    --eval-mode interval `
    --eval-interval 14
if ($LASTEXITCODE -ne 0) { throw "ns-train failed with exit code $LASTEXITCODE" }
