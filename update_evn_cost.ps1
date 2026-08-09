# Script cap nhat the Tieu Thu voi bieu gia dien 6 bac EVN
$storageFile = "d:\hieu-haos-v1\.storage\lovelace.nha_c_a_hi_u"
$yamlFile = "d:\hieu-haos-v1\dashboard_nha-c-a-hi-u.yaml"

$oldContentMarker = "var l_total = (p_total + g_imp_month).toFixed(1);"

$newJsCalc = @"
  var l_total = (p_total + g_imp_month).toFixed(1);
  function calcEvnCost(kwh) {
    var k = parseFloat(kwh) || 0;
    var c = 0;
    if (k <= 50) c = k * 1984;
    else if (k <= 100) c = 50 * 1984 + (k - 50) * 2050;
    else if (k <= 200) c = 50 * 1984 + 50 * 2050 + (k - 100) * 2380;
    else if (k <= 300) c = 50 * 1984 + 50 * 2050 + 100 * 2380 + (k - 200) * 2998;
    else if (k <= 400) c = 50 * 1984 + 50 * 2050 + 100 * 2380 + 100 * 2998 + (k - 300) * 3350;
    else c = 50 * 1984 + 50 * 2050 + 100 * 2380 + 100 * 2998 + 100 * 3350 + (k - 400) * 3460;
    return Math.round(c).toLocaleString('vi-VN');
  }
  var l_cost_month = calcEvnCost(l_total);
"@

Write-Host "Updating storage JSON and YAML file..."

# 1. Update in Storage JSON
$storageRaw = Get-Content $storageFile -Raw -Encoding UTF8
$storageJson = $storageRaw | ConvertFrom-Json

# In storage JSON, find all cards of custom:button-card containing 'TIÊU THỤ' and update content
$views = $storageJson.data.config.views
foreach ($v in $views) {
    foreach ($sec in $v.sections) {
        foreach ($card in $sec.cards) {
            # check if vertical-stack
            if ($card.cards) {
                foreach ($subCard in $card.cards) {
                    if ($subCard.custom_fields -and $subCard.custom_fields.content -match "TIÊU THỤ") {
                        Write-Host "Found TIÊU THỤ card in view: $($v.title)"
                        $content = $subCard.custom_fields.content
                        
                        # Replace calculation
                        if ($content -notmatch "calcEvnCost") {
                            $content = $content.Replace("var l_total = (p_total + g_imp_month).toFixed(1);", $newJsCalc)
                        }
                        
                        # Replace THÁNG NÀY HTML to include price
                        $oldThangNay = '<div style="font-size: 22px; font-weight: 800; color: #fff; margin-top: 2px; line-height: 1.1;">${l_total}</div>\n            <div style="font-size: 10px; color: #aaa; margin-top: 1px;">kWh</div>'
                        $newThangNay = '<div style="font-size: 20px; font-weight: 800; color: #fff; margin-top: 2px; line-height: 1.1;">${l_total} <span style="font-size: 10px; color: #aaa; font-weight: 400;">kWh</span></div>\n            <div style="font-size: 11px; color: #ffb74d; font-weight: 700; margin-top: 2px;">~${l_cost_month} đ</div>'
                        
                        $content = $content.Replace($oldThangNay, $newThangNay)
                        
                        # Also update HÔM NAY for nice alignment
                        $oldHomNay = '<div style="font-size: 22px; font-weight: 800; color: #fff; margin-top: 2px; line-height: 1.1;">${l_today}</div>\n            <div style="font-size: 10px; color: #aaa; margin-top: 1px;">kWh</div>'
                        $newHomNay = '<div style="font-size: 20px; font-weight: 800; color: #fff; margin-top: 2px; line-height: 1.1;">${l_today} <span style="font-size: 10px; color: #aaa; font-weight: 400;">kWh</span></div>\n            <div style="font-size: 10px; color: transparent; margin-top: 2px;">-</div>'
                        $content = $content.Replace($oldHomNay, $newHomNay)
                        
                        $subCard.custom_fields.content = $content
                    }
                }
            }
        }
    }
}

# Save updated storage JSON
$updatedJsonStr = $storageJson | ConvertTo-Json -Depth 100
[System.IO.File]::WriteAllText($storageFile, $updatedJsonStr, [System.Text.Encoding]::UTF8)

# Copy to HAOS storage directly
Copy-Item $storageFile "\\192.168.1.17\config\.storage\lovelace.nha_c_a_hi_u" -Force
Write-Host "✅ Copied updated lovelace.nha_c_a_hi_u to HAOS .storage!" -ForegroundColor Green
