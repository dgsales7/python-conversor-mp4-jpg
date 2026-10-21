# Conversor MP4 e JPG

Aplicativo para Windows feito em Python/Tkinter. Converte videos para MP4 e imagens para JPG, preservando subpastas e permitindo selecionar qualidade JPG.

## Gerar o executavel portatil (Windows)

1. Instale Python e FFmpeg no computador usado para **compilar**.
2. Verifique `ffmpeg -version` e `python --version` no terminal do PyCharm.
3. Deixe `conversor_unificado_portatil.py` e `gerar_exe.ps1` na mesma pasta.
4. No PowerShell dessa pasta, execute `powershell -ExecutionPolicy Bypass -File .\gerar_exe.ps1`.
5. Abra `dist\ConversorMP4_JPG.exe` e teste a conversao de um video e uma imagem.

O arquivo `.exe` inclui o Python, bibliotecas e `ffmpeg.exe`, e nao exige essas instalacoes no PC de destino. O primeiro inicio pode demorar alguns segundos. Teste em outro Windows compativel antes de distribuir. A compilacao para Windows deve ser feita no Windows.

## Publicar no GitHub

Envie o codigo-fonte, `gerar_exe.ps1`, `.gitignore` e este README para um repositorio Git. Publique o `.exe` como anexo de uma **Release**, nao como arquivo versionado no repositorio.

## FFmpeg

Confira a licenca da distribuicao FFmpeg que voce incluiu antes de redistribuir o executavel. As obrigacoes podem variar conforme a compilacao e codecs incluidos.
