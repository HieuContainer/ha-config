$lines = [System.IO.File]::ReadAllLines('d:\hieu-haos-v1\dashboard_nha-c-a-hi-u.yaml', [System.Text.Encoding]::UTF8)

# Find start of View 2 (Chế độ PC)
# Lines 1373 to 2727 (0-indexed: 1373 to 2727)
$pc_lines = $lines[1373..2727]

[System.IO.File]::WriteAllLines('d:\hieu-haos-v1\card_pc_full.yaml', $pc_lines, [System.Text.Encoding]::UTF8)
Write-Host "Exported card_pc_full.yaml with $($pc_lines.Length) lines"
