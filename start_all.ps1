
# Start tất cả các Bookstore Microservices
# Chạy script này từ thư mục c:\SAD\bookstore_micro bằng PowerShell

$root = "c:\SAD\bookstore_micro"
$python = "$root\book-service\venv\Scripts\python.exe"

# 1. Start DB
docker-compose -f "$root\docker-compose.yml" up -d
Start-Sleep -Seconds 3

# 2. Start mỗi service trong 1 terminal riêng
$services = @(
  @{dir="api_gateway";        port=8000},
  @{dir="book-service";       port=8001},
  @{dir="cart-service";       port=8002},
  @{dir="customer-service";   port=8003},
  @{dir="order-service";      port=8004},
  @{dir="pay-service";        port=8005},
  @{dir="ship-service";       port=8006},
  @{dir="catalog-service";    port=8007},
  @{dir="staff-service";      port=8008},
  @{dir="manager-service";    port=8009},
  @{dir="comment-service";    port=8010},
  @{dir="recommender-service";port=8011}
)

foreach ($svc in $services) {
  $dir = "$root\$($svc.dir)"
  Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$dir'; ..\book-service\venv\Scripts\python.exe manage.py runserver $($svc.port)" -WindowStyle Normal
  Start-Sleep -Milliseconds 500
}

Write-Host "=== TẤT CẢ SERVICES ĐÃ KHỞI ĐỘNG ==="
Write-Host "API Gateway:       http://localhost:8000/api/docs/"
Write-Host "Book Service:      http://localhost:8001/api/docs/"
Write-Host "Cart Service:      http://localhost:8002/api/docs/"
Write-Host "Customer Service:  http://localhost:8003/api/docs/"
Write-Host "Order Service:     http://localhost:8004/api/docs/"
Write-Host "Pay Service:       http://localhost:8005/api/docs/"
Write-Host "Ship Service:      http://localhost:8006/api/docs/"
Write-Host "Catalog Service:   http://localhost:8007/api/docs/"
Write-Host "Staff Service:     http://localhost:8008/api/docs/"
Write-Host "Manager Service:   http://localhost:8009/api/docs/"
Write-Host "Comment Service:   http://localhost:8010/api/docs/"
Write-Host "Recommender Svc:   http://localhost:8011/api/docs/"
Write-Host "Frontend:          c:\SAD\bookstore_micro\frontend\index.html"
