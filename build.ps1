param([string]$InnoCompiler = '')
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$pythonExe = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Unable to create the Python environment.' }
}
& $pythonExe -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& $PSScriptRoot\tools\make-icon.ps1
& $pythonExe app.py --self-test tools\source-report.json
if ($LASTEXITCODE -ne 0) { throw 'Source checks failed.' }
& $pythonExe tools\collect_licenses.py
if ($LASTEXITCODE -ne 0) { throw 'License collection failed.' }
& $pythonExe -m PyInstaller --noconfirm --clean --windowed --onedir --name ImageToPDF --icon assets\app.ico --add-data 'assets;assets' --add-data 'build\third-party-licenses;third-party-licenses' --collect-all pypdfium2 --collect-all pypdfium2_raw --version-file version_info.txt app.py
if ($LASTEXITCODE -ne 0) { throw 'Application build failed.' }
$reportPath = Join-Path $PSScriptRoot 'tools\frozen-report.json'
$testProcess = Start-Process -FilePath '.\dist\ImageToPDF\ImageToPDF.exe' -ArgumentList ('--self-test "' + $reportPath + '"') -WindowStyle Hidden -Wait -PassThru
if ($testProcess.ExitCode -ne 0) { throw 'Packaged application checks failed.' }
$report = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
if ($report.pdf_and_ui -ne 'passed' -or $report.multiple_processes -ne 'passed') { throw 'Incomplete packaged checks.' }
if (-not $InnoCompiler) {
    $candidates = @((Join-Path $PSScriptRoot 'tools\InnoSetup\ISCC.exe'), "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 7\ISCC.exe", "$env:LOCALAPPDATA\Programs\Inno Setup 7\ISCC.exe")
    $InnoCompiler = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $InnoCompiler) { throw 'Install Inno Setup and pass -InnoCompiler with the path to ISCC.exe.' }
& $InnoCompiler /Qp installer.iss
if ($LASTEXITCODE -ne 0) { throw 'Installer build failed.' }
Copy-Item -LiteralPath README.md,LICENSE -Destination dist\ImageToPDF
Compress-Archive -Path dist\ImageToPDF -DestinationPath release\ImageToPDF-Portable-2.1.1-x64.zip -Force
$hashLines = Get-ChildItem release -File | Where-Object { $_.Name -like '*-2.1.1-x64.*' -and $_.Extension -in '.exe', '.zip' } | Sort-Object Name | ForEach-Object { (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower() + '  ' + $_.Name }
Set-Content -LiteralPath release\SHA256SUMS.txt -Value $hashLines -Encoding ascii
Write-Host 'Build and packaged regression checks completed.'
