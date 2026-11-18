Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$lab = Join-Path $repo 'docs/public/access-log-monitoring/lab'
$script = Join-Path $lab 'Measure-AccessLog.ps1'
$sample = Join-Path $lab 'access.jsonl'
$checks = 0

function Assert-Equal($Actual, $Expected, [string]$Label) {
    if ($Actual -cne $Expected) { throw "${Label}: expected [$Expected], got [$Actual]" }
}

$expected = @(
    @('00:01:00', 10, 0, 0, 0, 180, 'OK'),
    @('00:02:00', 10, 3, 30, 4, 1800, 'ALERT'),
    @('00:03:00', 10, 0, 0, 0, 220, 'OK'),
    @('00:04:00', 0, 0, $null, 0, $null, 'NO_DATA'),
    @('00:00:15', 3, 0, 0, 0, 120, 'LOW_TRAFFIC')
)
foreach ($case in $expected) {
    $result = & $script -Path $sample -End "2026-11-18T$($case[0])Z"
    $fields = @('Requests', 'ServerErrors', 'ErrorRatePercent', 'SlowRequests', 'P95Ms', 'State')
    for ($i = 0; $i -lt $fields.Count; $i++) {
        Assert-Equal $result.($fields[$i]) $case[$i + 1] "$($case[0]) $($fields[$i])"
    }
    $checks++
}
$local = & $script -Path $sample -End '2026-11-18T09:02:00+09:00'
Assert-Equal $local.ServerErrors 3 'Timezone offset'
Assert-Equal $local.End '2026-11-18T00:02:00Z' 'UTC end'
$single = & $script -Path $sample -End '2026-11-18T00:00:01Z' -WindowSeconds 1
Assert-Equal $single.Requests 1 'Inclusive start / exclusive end'
$checks += 2

# Use isolated fixtures to exercise the two independent alert conditions.
$temp = Join-Path ([IO.Path]::GetTempPath()) ('access-log-test-' + [Guid]::NewGuid())
New-Item -ItemType Directory -Path $temp | Out-Null
try {
    $fixture = Join-Path $temp 'fixture.jsonl'
    $rows = @(Get-Content -LiteralPath $sample -Encoding UTF8 | Select-Object -First 10)
    foreach ($mode in @('errors', 'slow', 'below')) {
        $records = for ($i = 0; $i -lt 10; $i++) {
            $row = $rows[$i] | ConvertFrom-Json
            $row.status = 200
            $row.request_time_ms = 100
            if ($mode -eq 'errors' -and $i -lt 2) { $row.status = 500 }
            if ($mode -eq 'slow' -and $i -lt 3) { $row.request_time_ms = 1000 }
            if ($mode -eq 'below') {
                if ($i -eq 0) { $row.status = 500 }
                if ($i -lt 2) { $row.request_time_ms = 1000 }
            }
            $row | ConvertTo-Json -Compress
        }
        [IO.File]::WriteAllLines($fixture, [string[]]$records)
        $result = & $script -Path $fixture -End '2026-11-18T00:01:00Z'
        $state = 'ALERT'
        if ($mode -eq 'below') { $state = 'OK' }
        Assert-Equal $result.State $state "$mode threshold"
        $checks++
    }
    $invalid = @(
        '{broken',
        'null',
        '{}',
        ($rows[0] -replace '"status":200', '"status":"200"'),
        ($rows[0] -replace '"status":200', '"status":600'),
        ($rows[0] -replace '"request_time_ms":120', '"request_time_ms":-1'),
        ($rows[0] -replace '2026-11-18T00:00:00Z', '2026-11-18T00:00:00'),
        ($rows[0] -replace 'req-001', '')
    )
    foreach ($bad in $invalid) {
        [IO.File]::WriteAllLines($fixture, [string[]]@($rows[0], $bad))
        $message = $null
        try { & $script -Path $fixture -End '2026-11-18T00:01:00Z' | Out-Null }
        catch { $message = $_.Exception.Message }
        if ($null -eq $message -or $message -notlike 'Invalid log at line 2:*') {
            throw "Invalid input did not fail with line number: $bad ($message)"
        }
        $checks++
    }
}
finally {
    # Delete only the known fixture and its empty, uniquely named directory.
    if (Test-Path -LiteralPath $fixture) { Remove-Item -LiteralPath $fixture }
    Remove-Item -LiteralPath $temp
}
Write-Output "Access log checks passed: $checks"
