# Kraya Spring Boot startup — prompts for secrets with hidden input, never writes them to disk.
# Run from PowerShell: .\start-spring.ps1
# Requires JDK 21 at C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== Kraya Spring Boot — Secure Startup ===" -ForegroundColor Cyan
Write-Host "Rotate secrets BEFORE running if previous ones were exposed." -ForegroundColor Yellow
Write-Host ""

# --- Collect secrets via hidden input ---
$dbUser    = Read-Host "DATABASE_USERNAME (Supabase Session Pooler user, e.g. postgres.xxxxx)"
$dbPassSec = Read-Host "DATABASE_PASSWORD" -AsSecureString
$jwtSec    = Read-Host "JWT_SECRET (base64 or long random string)" -AsSecureString

# Decode SecureStrings to plain strings in memory only
$cred   = [System.Runtime.InteropServices.Marshal]::SecureStringToGlobalAllocUnicode($dbPassSec)
$dbPass = [System.Runtime.InteropServices.Marshal]::PtrToStringUni($cred)
[System.Runtime.InteropServices.Marshal]::ZeroFreeGlobalAllocUnicode($cred)

$credJ  = [System.Runtime.InteropServices.Marshal]::SecureStringToGlobalAllocUnicode($jwtSec)
$jwt    = [System.Runtime.InteropServices.Marshal]::PtrToStringUni($credJ)
[System.Runtime.InteropServices.Marshal]::ZeroFreeGlobalAllocUnicode($credJ)

# --- Set environment variables for this session only (not persisted) ---
$env:JAVA_HOME          = "C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot"
$env:DATABASE_URL       = "jdbc:postgresql://aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require"
$env:DATABASE_USERNAME  = $dbUser
$env:DATABASE_PASSWORD  = $dbPass
$env:JWT_SECRET         = $jwt
$env:SERVER_PORT        = "8081"
$env:AGENT_SERVICE_URL  = "http://127.0.0.1:8000"

# Clear plain-text variables immediately after env is set
$dbPass = $null; $jwt = $null

Write-Host ""
Write-Host "Starting Spring Boot on port 8081..." -ForegroundColor Green
Write-Host "DATABASE_URL  : $env:DATABASE_URL"
Write-Host "SERVER_PORT   : $env:SERVER_PORT"
Write-Host "AGENT_SERVICE_URL: $env:AGENT_SERVICE_URL"
Write-Host ""

Set-Location "c:\kraya - Agentic Procurement\backend\kraya-backend"
.\mvnw.cmd spring-boot:run "-Dspring-boot.run.jvmArguments=-Xmx256m"
