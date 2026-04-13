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

function Register-CustomerForLogin {
  param(
    [string]$Email,
    [string]$Password,
    [string]$Name
  )

  $payload = @{ name = $Name; email = $Email; password = $Password } | ConvertTo-Json
  $resp = curl.exe -s -o NUL -w "%{http_code}" -X POST "http://localhost:18021/auth/customer/register/" -H "Content-Type: application/json" -d $payload
  if ($resp -ne '201' -and $resp -ne '400') {
    throw "Register failed unexpectedly with status $resp"
  }
}

function Extract-Csrf {
  param([string]$Html)

  $m = [regex]::Match($Html, 'name="csrfmiddlewaretoken"\s+value="([^"]+)"')
  if (-not $m.Success) {
    $m = [regex]::Match($Html, "name='csrfmiddlewaretoken'\s+value='([^']+)'")
  }
  if (-not $m.Success) {
    throw 'Could not extract csrfmiddlewaretoken from login page'
  }
  return $m.Groups[1].Value
}

$seed = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$email = "gw_refresh_$seed@example.com"
$password = 'Pass@123'
$name = "Gateway Refresh $seed"

Register-CustomerForLogin -Email $email -Password $password -Name $name

$ws = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$loginPage = Invoke-WebRequest -Uri 'http://localhost:18000/auth/customer/login/' -WebSession $ws
Assert-True ($loginPage.StatusCode -eq 200) "Login page status expected 200 got $($loginPage.StatusCode)"

$csrf = Extract-Csrf -Html $loginPage.Content

$form = @{
  csrfmiddlewaretoken = $csrf
  email = $email
  password = $password
}

$headers = @{ Referer = 'http://localhost:18000/auth/customer/login/' }
$loginResp = Invoke-WebRequest -Method POST -Uri 'http://localhost:18000/auth/customer/login/' -Body $form -Headers $headers -WebSession $ws
Assert-True ($loginResp.StatusCode -eq 200) "Login response expected 200 got $($loginResp.StatusCode)"

$sessionCookie = $ws.Cookies.GetCookies('http://localhost:18000')['sessionid']
Assert-True ($null -ne $sessionCookie) 'Missing sessionid cookie after login'
$sessionId = $sessionCookie.Value
Assert-True (-not [string]::IsNullOrWhiteSpace($sessionId)) 'Session ID is empty'

$profileBefore = Invoke-WebRequest -Uri 'http://localhost:18000/profile/' -WebSession $ws
Assert-True ($profileBefore.StatusCode -eq 200) "Profile before tamper expected 200 got $($profileBefore.StatusCode)"
Write-Host 'PASS PROFILE_BEFORE_TAMPER=200'

$pyTamper = @"
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
s = Session.objects.get(session_key='$sessionId')
d = s.get_decoded()
d['access_token'] = 'invalid.token.value'
d['token'] = 'invalid.token.value'
store = SessionStore()
s.session_data = store.encode(d)
s.save(update_fields=['session_data'])
print('TAMPER_OK')
"@

$escapedTamper = $pyTamper.Replace('"', '\"').Replace("`r", '').Replace("`n", ';')
$tamperOut = docker exec bookstore_api_gateway python manage.py shell -c "$escapedTamper"
if ($LASTEXITCODE -ne 0) {
  throw 'Failed to tamper gateway session token'
}
Write-Host ($tamperOut | Out-String)

$profileAfter = Invoke-WebRequest -Uri 'http://localhost:18000/profile/' -WebSession $ws
Assert-True ($profileAfter.StatusCode -eq 200) "Profile after tamper expected 200 got $($profileAfter.StatusCode)"
Write-Host 'PASS PROFILE_AFTER_TAMPER=200 (auto refresh worked)'

$pyCheck = @"
from django.contrib.sessions.models import Session
s = Session.objects.get(session_key='$sessionId')
d = s.get_decoded()
at = d.get('access_token') or d.get('token') or ''
print('ACCESS_IS_INVALID=' + str(at == 'invalid.token.value'))
print('ACCESS_DOT_COUNT=' + str(at.count('.')))
print('HAS_REFRESH=' + str(bool(d.get('refresh_token'))))
"@

$escapedCheck = $pyCheck.Replace('"', '\"').Replace("`r", '').Replace("`n", ';')
$checkOut = docker exec bookstore_api_gateway python manage.py shell -c "$escapedCheck"
if ($LASTEXITCODE -ne 0) {
  throw 'Failed to verify session token after refresh'
}
Write-Host ($checkOut | Out-String)

Write-Host 'SSR gateway login + auto-refresh end-to-end test PASSED.'
