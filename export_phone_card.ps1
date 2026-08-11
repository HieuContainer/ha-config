$lines = [System.IO.File]::ReadAllLines('d:\hieu-haos-v1\dashboard_nha-c-a-hi-u.yaml', [System.Text.Encoding]::UTF8)
$stack = $lines[5..864]
$res = New-Object System.Collections.Generic.List[string]

$res.Add('type: vertical-stack')
$res.Add('cards:')

for ($i = 2; $i -lt $stack.Length; $i++) {
    $l = $stack[$i]
    if ($l.Length -ge 6) {
        $res.Add($l.Substring(6))
    } elseif ($l.Trim().Length -eq 0) {
        $res.Add('')
    } else {
        $res.Add($l.TrimStart())
    }
}

[System.IO.File]::WriteAllLines('d:\hieu-haos-v1\card_phone_full.yaml', $res, [System.Text.Encoding]::UTF8)
Write-Host "Exported card_phone_full.yaml with $($res.Count) lines"
