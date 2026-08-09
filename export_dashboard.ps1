# Script trich xuat cau hinh Dashboard tu .storage ra file dashboard_nha-c-a-hi-u.json va dashboard_nha-c-a-hi-u.yaml
$storagePath = "d:\hieu-haos-v1\.storage\lovelace.nha_c_a_hi_u"
$exportJsonPath = "d:\hieu-haos-v1\dashboard_nha-c-a-hi-u.json"

if (Test-Path $storagePath) {
    $raw = Get-Content $storagePath -Raw -Encoding UTF8
    $jsonObj = $raw | ConvertFrom-Json
    if ($jsonObj.data.config) {
        $configJson = $jsonObj.data.config | ConvertTo-Json -Depth 100
        [System.IO.File]::WriteAllText($exportJsonPath, $configJson, [System.Text.Encoding]::UTF8)
        Write-Host "✅ Da trich xuat cau hinh Dashboard moi nhat tu HAOS sang $exportJsonPath!" -ForegroundColor Green
    }
}
