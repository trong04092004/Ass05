@echo off
REM ============================================================
REM BookStore Microservices - Start All Services (Local Dev)
REM Ports: Gateway:8000, Customer:8003, Book:8001, Cart:8002
REM         Order:8004, Pay:8005, Ship:8006, Comment:8007
REM         Catalog:8008, Staff:8009, Manager:8010
REM
REM Truoc khi chay: bat Docker PostreSQL (port 5433)
REM   docker-compose up postgres -d
REM ============================================================

set ROOT=c:\SAD\bookstore_micro
set PYTHON=%ROOT%\book-service\venv\Scripts\python.exe
set DB_HOST=localhost
set DB_PORT=5433
set DB_USER=root
set DB_PASSWORD=rootpassword

echo Starting BookStore Microservices...

start "customer-service :8003" cmd /k "cd /d %ROOT%\customer-service && set DB_NAME=bookstore_micro_customer && set DB_HOST=%DB_HOST% && set DB_PORT=%DB_PORT% && set DB_USER=%DB_USER% && set DB_PASSWORD=%DB_PASSWORD% && %PYTHON% manage.py runserver 8003"

start "book-service :8001" cmd /k "cd /d %ROOT%\book-service && set DB_NAME=bookstore_micro_book && %PYTHON% manage.py runserver 8001"

start "cart-service :8002" cmd /k "cd /d %ROOT%\cart-service && set DB_NAME=bookstore_micro_cart && set BOOK_SERVICE_URL=http://localhost:8001 && %PYTHON% manage.py runserver 8002"

start "order-service :8004" cmd /k "cd /d %ROOT%\order-service && set DB_NAME=bookstore_micro_order && set CART_SERVICE_URL=http://localhost:8002 && set BOOK_SERVICE_URL=http://localhost:8001 && set PAY_SERVICE_URL=http://localhost:8005 && set SHIP_SERVICE_URL=http://localhost:8006 && %PYTHON% manage.py runserver 8004"

start "pay-service :8005" cmd /k "cd /d %ROOT%\pay-service && set DB_NAME=bookstore_micro_payment && %PYTHON% manage.py runserver 8005"

start "ship-service :8006" cmd /k "cd /d %ROOT%\ship-service && set DB_NAME=bookstore_micro_shipping && %PYTHON% manage.py runserver 8006"

start "comment-service :8007" cmd /k "cd /d %ROOT%\comment-service && set DB_NAME=bookstore_micro_rating && %PYTHON% manage.py runserver 8007"

start "catalog-service :8008" cmd /k "cd /d %ROOT%\catalog-service && set DB_NAME=bookstore_micro_catalog && %PYTHON% manage.py runserver 8008"

start "staff-service :8009" cmd /k "cd /d %ROOT%\staff-service && set DB_NAME=bookstore_micro_staff && %PYTHON% manage.py runserver 8009"

start "manager-service :8010" cmd /k "cd /d %ROOT%\manager-service && set DB_NAME=bookstore_micro_manager && %PYTHON% manage.py runserver 8010"

echo Waiting 5s for services to start...
timeout /t 5 /nobreak > NUL

start "API Gateway :8000" cmd /k "cd /d %ROOT%\api_gateway && set DB_NAME=bookstore_micro_gateway && set DB_HOST=%DB_HOST% && set DB_PORT=%DB_PORT% && set DB_USER=%DB_USER% && set DB_PASSWORD=%DB_PASSWORD% && set CUSTOMER_SERVICE_URL=http://localhost:8003 && set BOOK_SERVICE_URL=http://localhost:8001 && set CART_SERVICE_URL=http://localhost:8002 && set ORDER_SERVICE_URL=http://localhost:8004 && set PAY_SERVICE_URL=http://localhost:8005 && set SHIP_SERVICE_URL=http://localhost:8006 && set COMMENT_SERVICE_URL=http://localhost:8007 && set CATALOG_SERVICE_URL=http://localhost:8008 && set STAFF_SERVICE_URL=http://localhost:8009 && set MANAGER_SERVICE_URL=http://localhost:8010 && %PYTHON% manage.py runserver 8000"

echo.
echo ============================================================
echo  BookStore is starting up!
echo  Truy cap: http://localhost:8000
echo  Manager:  manager@bookstore.com / manager123
echo  Staff:    staff@bookstore.com / staff123
echo  Customer: customer1@example.com / cust123
echo ============================================================
