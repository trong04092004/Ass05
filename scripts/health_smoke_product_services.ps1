$ErrorActionPreference = 'Stop'

function Assert-True {
  param(
    [bool]$Condition,
    [string]$Message
  )
  if (-not $Condition) {
    throw $Message
  }
}

function Invoke-Json {
  param(
    [string]$Method,
    [string]$Url
  )
  $resp = Invoke-WebRequest -Method $Method -Uri $Url -TimeoutSec 15
  $body = $null
  if ($resp.Content) {
    $body = $resp.Content | ConvertFrom-Json
  }
  return [PSCustomObject]@{
    Status = [int]$resp.StatusCode
    Body = $body
  }
}

function Check-Service {
  param(
    [string]$Name,
    [string]$BaseUrl,
    [string]$ListPath,
    [string]$DetailPathTemplate
  )

  Write-Host "=== CHECK $Name ==="

  $health = Invoke-Json -Method GET -Url "$BaseUrl/health/security/"
  Assert-True ($health.Status -eq 200) "$Name health endpoint failed with $($health.Status)"
  Assert-True (-not [string]::IsNullOrWhiteSpace($health.Body.jwt_key_fingerprint)) "$Name missing jwt_key_fingerprint"
  Write-Host "PASS health/security"

  $list = Invoke-Json -Method GET -Url "$BaseUrl$ListPath"
  Assert-True ($list.Status -eq 200) "$Name list endpoint failed with $($list.Status)"

  $items = @()
  if ($list.Body -is [System.Array]) {
    $items = $list.Body
  } elseif ($null -ne $list.Body.results) {
    $items = $list.Body.results
  }

  $count = $items.Count
  Assert-True ($count -ge 10) "$Name expected >= 10 items but got $count"

  $missingImage = 0
  foreach ($it in $items) {
    if ($null -eq $it.image_url -or [string]::IsNullOrWhiteSpace([string]$it.image_url)) {
      $missingImage++
    }
  }
  Assert-True ($missingImage -eq 0) "$Name has $missingImage items missing image_url"
  Write-Host "PASS list count=$count and full images"

  $first = $items | Select-Object -First 1
  Assert-True ($null -ne $first) "$Name no item for detail smoke"
  $detailPath = $DetailPathTemplate.Replace('{id}', [string]$first.id)
  $detail = Invoke-Json -Method GET -Url "$BaseUrl$detailPath"
  Assert-True ($detail.Status -eq 200) "$Name detail endpoint failed with $($detail.Status)"
  Write-Host "PASS detail smoke id=$($first.id)"
}

$services = @(
  @{name='book-service'; base='http://localhost:18002'; list='/books/'; detail='/books/{id}/'},
  @{name='electronics-service'; base='http://localhost:18012'; list='/products/'; detail='/products/{id}/'},
  @{name='fashion-service'; base='http://localhost:18013'; list='/products/'; detail='/products/{id}/'},
  @{name='toy-service'; base='http://localhost:18014'; list='/products/'; detail='/products/{id}/'},
  @{name='grocery-service'; base='http://localhost:18015'; list='/products/'; detail='/products/{id}/'},
  @{name='furniture-service'; base='http://localhost:18016'; list='/products/'; detail='/products/{id}/'},
  @{name='beauty-service'; base='http://localhost:18017'; list='/products/'; detail='/products/{id}/'},
  @{name='sports-service'; base='http://localhost:18018'; list='/products/'; detail='/products/{id}/'},
  @{name='pet-service'; base='http://localhost:18019'; list='/products/'; detail='/products/{id}/'},
  @{name='stationery-service'; base='http://localhost:18020'; list='/products/'; detail='/products/{id}/'}
)

foreach ($svc in $services) {
  Check-Service -Name $svc.name -BaseUrl $svc.base -ListPath $svc.list -DetailPathTemplate $svc.detail
}

Write-Host "ALL PRODUCT SERVICE HEALTH + SMOKE TESTS PASSED"