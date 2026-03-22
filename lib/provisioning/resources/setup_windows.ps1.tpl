# setup_windows.ps1 - Mad Max server emulator setup for Windows client
# Run in PowerShell as Administrator:
#   Set-ExecutionPolicy Bypass -Scope Process
#   .\setup_windows.ps1

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProxyIP = "__LAN_IP__"

Write-Host "=== Mad Max - Windows Client Setup ===" -ForegroundColor Cyan

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).
    IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    throw "Run setup_windows.ps1 as Administrator."
}

# Step 1: Install CA certificate to the Windows Root store
Write-Host "[1/2] Installing CA certificate..."
$certContent = @"
__CA_PEM__
"@
$certPath = "$env:TEMP\localproxy_ca.crt"
$certContent | Out-File -Encoding ASCII $certPath
$certInfo = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($certPath)
$thumbprint = $certInfo.Thumbprint

$certutilOutput = certutil -addstore -f Root $certPath 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "certutil failed: $($certutilOutput | Out-String)"
}

$installed = Get-ChildItem Cert:\LocalMachine\Root | Where-Object { $_.Thumbprint -eq $thumbprint }
if (-not $installed) {
    throw "CA certificate with thumbprint $thumbprint was not found in LocalMachine\\Root after import."
}
Write-Host "      OK: CA installed to Windows Root Store ($thumbprint)"

# Step 2: Point DNS to the proxy server
Write-Host "[2/2] Configuring DNS..."
$defaultRoute = Get-NetRoute -AddressFamily IPv4 -DestinationPrefix "0.0.0.0/0" |
    Sort-Object RouteMetric, InterfaceMetric |
    Select-Object -First 1
if (-not $defaultRoute) {
    throw "Could not determine the active IPv4 default route."
}

$adapter = Get-NetAdapter -InterfaceIndex $defaultRoute.InterfaceIndex
if (-not $adapter -or $adapter.Status -ne "Up") {
    throw "Could not determine the active network adapter."
}

$previousDns = (Get-DnsClientServerAddress -InterfaceIndex $adapter.InterfaceIndex -AddressFamily IPv4).ServerAddresses
Set-DnsClientServerAddress -InterfaceIndex $adapter.InterfaceIndex `
    -ServerAddresses @("__LAN_IP__", "8.8.8.8")
$currentDns = (Get-DnsClientServerAddress -InterfaceIndex $adapter.InterfaceIndex -AddressFamily IPv4).ServerAddresses
Write-Host "      OK: DNS set to __LAN_IP__ on $($adapter.Name)"
Write-Host "      Previous DNS: $($previousDns -join ', ')"
Write-Host "      Current DNS : $($currentDns -join ', ')"

Write-Host ""
Write-Host "=== Setup complete! ===" -ForegroundColor Green
Write-Host "Make sure local_proxy.py is running on __LAN_IP__, then launch Mad Max."
Write-Host ""
Write-Host "To revert DNS:"
Write-Host "  Set-DnsClientServerAddress -InterfaceIndex $($adapter.InterfaceIndex) -ResetServerAddresses"
