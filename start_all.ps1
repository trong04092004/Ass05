
# Start tất cả các Bookstore Microservices
# Chạy script này trực tiếp từ workspace Bookstore bằng PowerShell

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Start DB
docker-compose -f "$root\docker-compose.yml" up -d
Start-Sleep -Seconds 3

# 2. Start mỗi service trong 1 terminal riêng
$services = @(
  @{dir = "api_gateway"; port = 8000 },
  @{dir = "book-service"; port = 8001 },
  @{dir = "cart-service"; port = 8002 },
  @{dir = "customer-service"; port = 8003 },
  @{dir = "order-service"; port = 8004 },
  @{dir = "pay-service"; port = 8005 },
  @{dir = "ship-service"; port = 8006 },
  @{dir = "catalog-service"; port = 8007 },
  @{dir = "staff-service"; port = 8008 },
  @{dir = "manager-service"; port = 8009 },
  @{dir = "comment-service"; port = 8010 },
  @{dir = "auth-service"; port = 8021 },
  @{dir = "AI-serivce"; port = 8011 },
  @{dir = "electronics-service"; port = 8012 },
  @{dir = "fashion-service"; port = 8013 },
  @{dir = "toy-service"; port = 8014 },
  @{dir = "grocery-service"; port = 8015 },
  @{dir = "furniture-service"; port = 8016 },
  @{dir = "beauty-service"; port = 8017 },
  @{dir = "sports-service"; port = 8018 },
  @{dir = "pet-service"; port = 8019 },
  @{dir = "stationery-service"; port = 8020 }
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
Write-Host "Auth Service:      http://localhost:8021/api/docs/"
Write-Host "AI Service:        http://localhost:8011/api/docs/"
Write-Host "Electronics Svc:   http://localhost:8012/api/docs/"
Write-Host "Fashion Svc:       http://localhost:8013/api/docs/"
Write-Host "Toy Svc:           http://localhost:8014/api/docs/"
Write-Host "Grocery Svc:       http://localhost:8015/api/docs/"
Write-Host "Furniture Svc:     http://localhost:8016/api/docs/"
Write-Host "Beauty Svc:        http://localhost:8017/api/docs/"
Write-Host "Sports Svc:        http://localhost:8018/api/docs/"
Write-Host "Pet Svc:           http://localhost:8019/api/docs/"
Write-Host "Stationery Svc:    http://localhost:8020/api/docs/"
Write-Host "Frontend React:    http://localhost:5173 (run: cd Frontend; npm run dev)"
