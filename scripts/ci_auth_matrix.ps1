$ErrorActionPreference = 'Stop'

function Get-StatusCode {
  param(
    [string]$Method,
    [string]$Url,
    [string]$Token = $null,
    [object]$Body = $null
  )

  try {
    $headers = @{}
    if ($Token) {
      $headers['Authorization'] = "Bearer $Token"
    }

    if ($null -ne $Body) {
      $json = ($Body | ConvertTo-Json -Depth 10)
      $resp = Invoke-WebRequest -Method $Method -Uri $Url -Headers $headers -ContentType 'application/json' -Body $json
    } else {
      $resp = Invoke-WebRequest -Method $Method -Uri $Url -Headers $headers
    }

    return @{ status = [int]$resp.StatusCode; body = $resp.Content }
  } catch {
    $code = 0
    $content = ''

    if ($_.Exception.Response) {
      $code = [int]$_.Exception.Response.StatusCode.value__
      try {
        $sr = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $content = $sr.ReadToEnd()
      } catch {
      }
    }

    return @{ status = $code; body = $content }
  }
}

function Assert-Status {
  param(
    [string]$Name,
    [int]$Expected,
    [int]$Got
  )

  if ($Expected -ne $Got) {
    throw "$Name expected=$Expected got=$Got"
  }
  Write-Host "PASS $Name = $Got"
}

$base = @{
  auth = 'http://localhost:18021'
  customer = 'http://localhost:18001'
  book = 'http://localhost:18002'
  cart = 'http://localhost:18003'
  order = 'http://localhost:18004'
  pay = 'http://localhost:18005'
  ship = 'http://localhost:18006'
  comment = 'http://localhost:18007'
  catalog = 'http://localhost:18008'
  staff = 'http://localhost:18009'
  manager = 'http://localhost:18010'
}

foreach ($k in $base.Keys) {
  $r = Get-StatusCode -Method GET -Url "$($base[$k])/health/security/"
  Assert-Status -Name "HEALTH_$k" -Expected 200 -Got $r.status
  $obj = $r.body | ConvertFrom-Json
  if (-not $obj.jwt_key_fingerprint) {
    throw "HEALTH_$k missing jwt_key_fingerprint"
  }
  Write-Host "PASS HEALTH_PAYLOAD_$k service=$($obj.service) fingerprint=$($obj.jwt_key_fingerprint)"
}

function Register-Customer {
  param([string]$suffix)

  $payload = @{
    name = "Customer $suffix"
    email = "customer_$suffix@example.com"
    password = 'Pass@123'
  }

  $r = Get-StatusCode -Method POST -Url "$($base.auth)/auth/customer/register/" -Body $payload
  Assert-Status -Name "REGISTER_CUSTOMER_$suffix" -Expected 201 -Got $r.status
  $obj = $r.body | ConvertFrom-Json
  return @{ token = $obj.access; customer_id = [int]$obj.customer_id }
}

function Register-Manager {
  param([string]$suffix)

  $payload = @{
    name = "Manager $suffix"
    email = "manager_$suffix@example.com"
    password = 'Pass@123'
    role = 'manager'
  }

  $r = Get-StatusCode -Method POST -Url "$($base.auth)/auth/admin/register/" -Body $payload
  Assert-Status -Name "REGISTER_MANAGER_$suffix" -Expected 201 -Got $r.status
  $obj = $r.body | ConvertFrom-Json
  return $obj.access
}

function Run-Matrix {
  param([string]$tag)

  Write-Host "===== MATRIX ROUND $tag ====="

  $c1 = Register-Customer -suffix "a_$tag"
  $c2 = Register-Customer -suffix "b_$tag"
  $mToken = Register-Manager -suffix "m_$tag"

  Assert-Status -Name 'BOOK_GET_PUBLIC' -Expected 200 -Got (Get-StatusCode -Method GET -Url "$($base.book)/books/").status
  Assert-Status -Name 'BOOK_POST_NOAUTH' -Expected 401 -Got (Get-StatusCode -Method POST -Url "$($base.book)/books/" -Body @{ title = 'Denied'; author = 'CI'; price = '10.00'; stock = 1 }).status

  Assert-Status -Name 'CART_GET_NOAUTH' -Expected 401 -Got (Get-StatusCode -Method GET -Url "$($base.cart)/carts/$($c1.customer_id)/").status
  Assert-Status -Name 'CART_GET_OWNER' -Expected 200 -Got (Get-StatusCode -Method GET -Url "$($base.cart)/carts/$($c1.customer_id)/" -Token $c1.token).status
  Assert-Status -Name 'CART_GET_OTHER' -Expected 403 -Got (Get-StatusCode -Method GET -Url "$($base.cart)/carts/$($c1.customer_id)/" -Token $c2.token).status

  Assert-Status -Name 'ORDER_POST_NOAUTH' -Expected 401 -Got (Get-StatusCode -Method POST -Url "$($base.order)/orders/" -Body @{ customer_id = $c1.customer_id }).status
  Assert-Status -Name 'ORDER_POST_MISMATCH' -Expected 403 -Got (Get-StatusCode -Method POST -Url "$($base.order)/orders/" -Token $c1.token -Body @{ customer_id = $c2.customer_id }).status

  Assert-Status -Name 'PROMO_POST_CUSTOMER' -Expected 403 -Got (Get-StatusCode -Method POST -Url "$($base.manager)/promotions/" -Token $c1.token -Body @{ name = 'Nope'; discount_percent = 5 }).status
  Assert-Status -Name 'PROMO_POST_MANAGER' -Expected 201 -Got (Get-StatusCode -Method POST -Url "$($base.manager)/promotions/" -Token $mToken -Body @{ name = "Promo $tag"; discount_percent = 10 }).status

  Assert-Status -Name 'PAYMENT_LIST_CUSTOMER' -Expected 403 -Got (Get-StatusCode -Method GET -Url "$($base.pay)/payments/" -Token $c1.token).status
  Assert-Status -Name 'PAYMENT_LIST_MANAGER' -Expected 200 -Got (Get-StatusCode -Method GET -Url "$($base.pay)/payments/" -Token $mToken).status

  Assert-Status -Name 'CUSTOMER_DETAIL_NOAUTH' -Expected 401 -Got (Get-StatusCode -Method GET -Url "$($base.customer)/customers/$($c1.customer_id)/").status
  Assert-Status -Name 'CUSTOMER_DETAIL_OWNER' -Expected 200 -Got (Get-StatusCode -Method GET -Url "$($base.customer)/customers/$($c1.customer_id)/" -Token $c1.token).status
  Assert-Status -Name 'CUSTOMER_DETAIL_OTHER' -Expected 403 -Got (Get-StatusCode -Method GET -Url "$($base.customer)/customers/$($c1.customer_id)/" -Token $c2.token).status

  Assert-Status -Name 'RATING_POST_NOAUTH' -Expected 401 -Got (Get-StatusCode -Method POST -Url "$($base.comment)/ratings/" -Body @{ book_id = 1; customer_id = $c1.customer_id; rating = 5; comment = 'ci' }).status
  Assert-Status -Name 'RATING_POST_AUTH' -Expected 201 -Got (Get-StatusCode -Method POST -Url "$($base.comment)/ratings/" -Token $c1.token -Body @{ book_id = 1; customer_id = $c1.customer_id; rating = 5; comment = 'ci' }).status
}

$ts = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
Run-Matrix -tag "$ts-r1"
Start-Sleep -Seconds 2
Run-Matrix -tag "$ts-r2"

Write-Host 'ALL JWT/Permission STABILITY CHECKS PASSED (2 rounds).'
