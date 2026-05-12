@echo off
setlocal
set ROOT=%~dp0
if "%ROOT:~-1%"=="\" set ROOT=%ROOT:~0,-1%
cd /d %ROOT%

echo Starting Docker stack...
docker compose up -d --build
if errorlevel 1 (
  echo Failed to start Docker stack.
  exit /b 1
)

echo.
echo Services:
echo   API Gateway : http://localhost:18000
echo   AI Service  : http://localhost:18009
echo   Frontend    : http://localhost:15173
echo   PostgreSQL  : localhost:5432
echo   Neo4j       : http://localhost:7474
endlocal
