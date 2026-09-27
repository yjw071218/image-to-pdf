$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$projectDir = Split-Path $PSScriptRoot
$sourceImage = [System.Drawing.Image]::FromFile((Join-Path $projectDir 'assets\logo.png'))
$iconFrames = @()
try {
    foreach ($size in @(16, 24, 32, 48, 64, 128, 256)) {
        $bitmap = New-Object System.Drawing.Bitmap($size, $size)
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $graphics.DrawImage($sourceImage, 0, 0, $size, $size)
        $buffer = New-Object System.IO.MemoryStream
        $bitmap.Save($buffer, [System.Drawing.Imaging.ImageFormat]::Png)
        $iconFrames += ,@{ Size = $size; Bytes = $buffer.ToArray() }
        $buffer.Dispose()
        $graphics.Dispose()
        $bitmap.Dispose()
    }
    $stream = [System.IO.File]::Create((Join-Path $projectDir 'assets\app.ico'))
    $writer = New-Object System.IO.BinaryWriter($stream)
    try {
        $writer.Write([uint16]0)
        $writer.Write([uint16]1)
        $writer.Write([uint16]$iconFrames.Count)
        $offset = 6 + 16 * $iconFrames.Count
        foreach ($frame in $iconFrames) {
            $dimension = if ($frame.Size -eq 256) { 0 } else { $frame.Size }
            $writer.Write([byte]$dimension)
            $writer.Write([byte]$dimension)
            $writer.Write([byte]0)
            $writer.Write([byte]0)
            $writer.Write([uint16]1)
            $writer.Write([uint16]32)
            $writer.Write([uint32]$frame.Bytes.Length)
            $writer.Write([uint32]$offset)
            $offset += $frame.Bytes.Length
        }
        foreach ($frame in $iconFrames) { $writer.Write([byte[]]$frame.Bytes) }
    } finally { $writer.Dispose(); $stream.Dispose() }
} finally { $sourceImage.Dispose() }
