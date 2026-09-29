param([switch]$Force)
$ErrorActionPreference='Stop'
$assets=$PSScriptRoot+'\assets'
$modelName='yolox.onnx'
$modelUrl='https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/object_detection_yolox/object_detection_yolox_2022nov.onnx'
$modelHash='c5c2d13e59ae883e6af3b45daea64af4833a4951c92d116ec270d9ddbe998063'
$downloads=@(
    @{Name='zidane.jpg';Url='https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/assets/zidane.jpg'},
    @{Name='bus.jpg';Url='https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/assets/bus.jpg'},
    @{Name='fruits.jpg';Url='https://raw.githubusercontent.com/opencv/opencv/master/samples/data/fruits.jpg'}
)
New-Item -ItemType Directory -Path $assets -Force | Out-Null
function Get-Asset($name,$url) {
    $destination=Join-Path $assets $name
    if((Test-Path -LiteralPath $destination) -and -not $Force){
        if($name -ne $modelName){return}
        $existing=(Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
        if($existing -eq $modelHash){return}
    }
    $temporary=$destination+'.download'
    Invoke-WebRequest -Uri $url -OutFile $temporary
    if($name -eq $modelName) {
        $actual=(Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash.ToLowerInvariant()
        if($actual -ne $modelHash){Remove-Item -LiteralPath $temporary;throw "Model SHA-256 mismatch: $actual"}
    }
    Move-Item -LiteralPath $temporary -Destination $destination -Force
}
Get-Asset $modelName $modelUrl
foreach($asset in $downloads){Get-Asset $asset.Name $asset.Url}
Write-Output 'Model and public validation images are ready in assets/.'
