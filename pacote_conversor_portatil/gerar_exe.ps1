$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (-not (Test-Path '.\conversor_unificado_portatil.py')) {
    throw 'Arquivo conversor_unificado_portatil.py nao encontrado nesta pasta.'
}

$ffmpeg = (Get-Command ffmpeg.exe -ErrorAction SilentlyContinue).Source
if (-not $ffmpeg) {
    throw 'ffmpeg.exe nao encontrado no PATH. Instale o FFmpeg ou configure o PATH e abra um novo terminal.'
}

Write-Host "FFmpeg localizado: $ffmpeg"
python -m pip install --upgrade pyinstaller pillow pillow-heif
if ($LASTEXITCODE -ne 0) { throw 'Falha na instalacao das dependencias.' }

python -m PyInstaller --noconfirm --clean --onefile --windowed --name ConversorMP4_JPG --collect-all pillow_heif --add-binary "$($ffmpeg);." .\conversor_unificado_portatil.py
if ($LASTEXITCODE -ne 0) { throw 'Falha ao gerar executavel.' }

Write-Host "Executavel gerado: $PSScriptRoot\dist\ConversorMP4_JPG.exe" -ForegroundColor Green
