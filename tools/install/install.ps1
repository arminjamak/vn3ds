# vn3ds for Windows: port a Ren'Py visual novel to the 3DS and put it there.
#
# In PowerShell (Windows PowerShell 5.1 or PowerShell 7), all on one line:
#
#   & ([scriptblock]::Create([Text.Encoding]::UTF8.GetString((iwr -useb https://arminjamak.github.io/vn3ds/install.ps1).RawContentStream.ToArray()))) <your game>
#
# Type the command, drag the game (folder, .zip or .apk) into the window and
# press Enter. Without a game it asks for one. (The command reads the script
# as bytes and decodes it itself, so it works however the server labels it.)
#
# The first time, this downloads the vn3ds-port program (about 80 MB) into
# %LOCALAPPDATA%\vn3ds\cli; afterwards it is only downloaded again when there
# is a new release. Then it runs it on the game.
#
# $env:VN3DS_DOWNLOAD_URL replaces where the download comes from (for testing).
# This file is plain ASCII on purpose (no byte order mark).

param([Parameter(ValueFromRemainingArguments = $true)][string[]]$GameArgs)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'   # Windows PowerShell's progress bar makes downloads crawl

$DownloadUrl = 'https://github.com/arminjamak/vn3ds/releases/latest/download'
if ($env:VN3DS_DOWNLOAD_URL) { $DownloadUrl = $env:VN3DS_DOWNLOAD_URL }

# Never `exit`: this runs inside the user's own PowerShell session, which
# exit would close. Problems are thrown and reported at the end.
function Fail([string]$msg) {
    throw "vn3ds: $msg"
}

# Windows PowerShell 5.1 may not offer TLS 1.2 by default.
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
} catch { }

function Get-Text([string]$url) {
    # Bytes, decoded here: the server may call any file application/octet-stream.
    $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 20
    return [Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray())
}

# Something that changes when a new release is published: GitHub redirects
# .../latest/download/<asset> to the release's own URL.
function Get-ReleaseKey([string]$url) {
    try {
        $r = Invoke-WebRequest -Uri $url -Method Head -UseBasicParsing -TimeoutSec 20
    } catch {
        return $null
    }
    $final = $null
    if ($r.BaseResponse.PSObject.Properties['ResponseUri']) {            # 5.1
        $final = $r.BaseResponse.ResponseUri.AbsoluteUri
    } elseif ($r.BaseResponse.PSObject.Properties['RequestMessage']) {   # 7
        $final = $r.BaseResponse.RequestMessage.RequestUri.AbsoluteUri
    }
    $parts = @($final)
    foreach ($h in 'Content-Length', 'ETag', 'Last-Modified') {
        if ($r.Headers[$h]) { $parts += ($r.Headers[$h] -join ',') }
    }
    return ($parts -join ' ')
}

function Install-Cli([string]$dir) {
    $asset = 'vn3ds-cli-windows-x64.zip'
    $url = "$DownloadUrl/$asset"
    $exe = Join-Path $dir 'vn3ds\vn3ds-port.exe'
    $stamp = Join-Path $dir 'release'
    $key = Get-ReleaseKey $url
    if (Test-Path $exe) {
        if (-not $key) {
            Write-Host "vn3ds: can't check for a newer version (offline?); using the one already here"
            return $exe
        }
        if ((Test-Path $stamp) -and ((Get-Content -Raw $stamp) -eq $key)) { return $exe }
    }
    if (-not $key) { Fail "can't reach $url" }
    Write-Host "Downloading vn3ds ($asset)..."
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $tmp = Join-Path $dir ('download-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $tmp | Out-Null
    try {
        $zip = Join-Path $tmp $asset
        Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
        $sum = $null
        try { $sum = Get-Text "$url.sha256" } catch { }
        if ($sum) {
            $want = ($sum.Trim() -split '\s+')[0].ToUpperInvariant()
            $got = (Get-FileHash -Algorithm SHA256 -Path $zip).Hash.ToUpperInvariant()
            if ($want -ne $got) { Fail 'the download is damaged (checksum mismatch); please try again' }
        }
        $unpacked = Join-Path $tmp 'unpacked'
        Expand-Archive -Path $zip -DestinationPath $unpacked -Force
        if (-not (Test-Path (Join-Path $unpacked 'vn3ds\vn3ds-port.exe'))) {
            Fail "$asset doesn't contain vn3ds\vn3ds-port.exe"
        }
        $old = Join-Path $dir 'vn3ds'
        if (Test-Path $old) { Remove-Item -Recurse -Force $old }
        Move-Item (Join-Path $unpacked 'vn3ds') $old
        [IO.File]::WriteAllText($stamp, $key)
    } finally {
        Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
    }
    return $exe
}

try {
    if (-not [Environment]::Is64BitOperatingSystem) { Fail 'vn3ds needs 64-bit Windows' }
    $base = $env:LOCALAPPDATA
    if (-not $base) { $base = Join-Path $env:USERPROFILE 'AppData\Local' }
    $exe = Install-Cli (Join-Path $base 'vn3ds\cli')
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    $global:LASTEXITCODE = 1
    return
}

# Paths as they arrive when a file is dragged into the window: PowerShell has
# already removed the quotes. A trailing backslash would make Windows
# PowerShell 5.1 pass a stray quote to the program, so it goes.
$pass = @()
foreach ($a in $GameArgs) {
    if ($null -eq $a) { continue }
    $p = $a.Trim()
    if ($p.Length -ge 2 -and (($p[0] -eq '"' -and $p[-1] -eq '"') -or ($p[0] -eq "'" -and $p[-1] -eq "'"))) {
        $p = $p.Substring(1, $p.Length - 2)
    }
    if ($p.Length -gt 3 -and $p.EndsWith('\')) { $p = $p.TrimEnd('\') }
    if ($p) { $pass += $p }
}
& $exe @pass
