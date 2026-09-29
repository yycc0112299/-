param(
    [Parameter(Mandatory=$true)]
    [string[]]$Files,

    [Parameter(Mandatory=$true)]
    [string]$OutputDir,

    [int]$LinesPerImage = 18
)

Add-Type -AssemblyName System.Drawing

$resolvedOutput = Resolve-Path -LiteralPath $OutputDir -ErrorAction SilentlyContinue
if (-not $resolvedOutput) {
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
    $resolvedOutput = Resolve-Path -LiteralPath $OutputDir
}

$font = [System.Drawing.Font]::new("Consolas", 16, [System.Drawing.FontStyle]::Regular)
$titleFont = [System.Drawing.Font]::new("Segoe UI", 18, [System.Drawing.FontStyle]::Bold)
$brushText = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(226, 232, 240))
$brushTitle = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(248, 250, 252))
$brushLineNo = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(148, 163, 184))
$brushBg = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(15, 23, 42))
$brushHeader = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(30, 41, 59))

foreach ($file in $Files) {
    $path = Resolve-Path -LiteralPath $file
    $lines = Get-Content -LiteralPath $path.Path
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($path.Path)

    for ($start = 0; $start -lt $lines.Count; $start += $LinesPerImage) {
        $end = [Math]::Min($start + $LinesPerImage - 1, $lines.Count - 1)
        $imageIndex = [int]($start / $LinesPerImage) + 1
        $fileName = "{0}_{1:D2}_{2:D3}-{3:D3}.png" -f $baseName, $imageIndex, ($start + 1), ($end + 1)
        $outPath = Join-Path $resolvedOutput.Path $fileName

        $width = 1500
        $height = 120 + (($end - $start + 1) * 30)
        $bmp = [System.Drawing.Bitmap]::new($width, $height)
        $graphics = [System.Drawing.Graphics]::FromImage($bmp)
        $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit
        $graphics.FillRectangle($brushBg, 0, 0, $width, $height)
        $graphics.FillRectangle($brushHeader, 0, 0, $width, 70)

        $title = "{0}  lines {1}-{2}" -f ([System.IO.Path]::GetFileName($path.Path)), ($start + 1), ($end + 1)
        $graphics.DrawString($title, $titleFont, $brushTitle, 28, 20)

        $y = 90
        for ($i = $start; $i -le $end; $i++) {
            $lineNo = "{0,3}" -f ($i + 1)
            $graphics.DrawString($lineNo, $font, $brushLineNo, 28, $y)
            $graphics.DrawString($lines[$i], $font, $brushText, 92, $y)
            $y += 30
        }

        $bmp.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
        $graphics.Dispose()
        $bmp.Dispose()
    }
}

$font.Dispose()
$titleFont.Dispose()
$brushText.Dispose()
$brushTitle.Dispose()
$brushLineNo.Dispose()
$brushBg.Dispose()
$brushHeader.Dispose()
