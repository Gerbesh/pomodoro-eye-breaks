param(
  [string]$FilePath = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..")) "release\FocusBreaks.exe"),
  [string]$Subject = "CN=Gerbesh Focus Breaks Self-Signed Code Signing",
  [string]$TimestampServer = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"

$Cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert |
  Where-Object { $_.Subject -eq $Subject } |
  Sort-Object NotAfter -Descending |
  Select-Object -First 1

if (-not $Cert) {
  $Cert = New-SelfSignedCertificate `
    -Type CodeSigningCert `
    -Subject $Subject `
    -CertStoreLocation Cert:\CurrentUser\My `
    -KeyUsage DigitalSignature `
    -FriendlyName "Focus Breaks Self-Signed Code Signing"
}

$Signature = Set-AuthenticodeSignature `
  -FilePath (Resolve-Path $FilePath) `
  -Certificate $Cert `
  -TimestampServer $TimestampServer

$Signature | Format-List Status, StatusMessage, SignerCertificate, TimeStamperCertificate
