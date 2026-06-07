# deploy.ps1 — Automates Docker build and push to Docker Hub

param(
    [string]$ImageName = "gdrive-search",
    [string]$Tag = "latest"
)

$DockerUsername = $env:DOCKER_USERNAME

if (-not $DockerUsername) {
    Write-Error "DOCKER_USERNAME environment variable not set"
    exit 1
}
$FullTag = "$DockerUsername/$ImageName`:$Tag"

Write-Host "Building Docker image: $FullTag" -ForegroundColor Cyan
docker build -t $FullTag .

if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker build failed"
    exit 1
}

Write-Host "Pushing to Docker Hub: $FullTag" -ForegroundColor Cyan
docker push $FullTag

if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker push failed"
    exit 1
}

Write-Host "Done! Image pushed: $FullTag" -ForegroundColor Green