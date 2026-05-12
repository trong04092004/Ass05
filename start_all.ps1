# Start full Docker stack (current services only)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host "Starting Docker stack..."
docker compose up -d --build

Write-Host ""
Write-Host "Services:"
Write-Host "  API Gateway : http://localhost:18000"
Write-Host "  AI Service  : http://localhost:18009"
Write-Host "  Frontend    : http://localhost:15173"
Write-Host "  PostgreSQL  : localhost:5432"
Write-Host "  Neo4j       : http://localhost:7474"
