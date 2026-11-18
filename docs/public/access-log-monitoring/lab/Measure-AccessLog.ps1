param(
    [Parameter(Mandatory = $true)][string]$Path,
    [string]$End = [DateTimeOffset]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ'),
    [ValidateRange(1, 86400)][int]$WindowSeconds = 60
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function ConvertTo-LogTime($Value) {
    # Older PowerShell releases deserialize JSON timestamps as DateTime.
    if ($Value -is [DateTime]) {
        if ($Value.Kind -eq [DateTimeKind]::Unspecified) { throw 'A timezone is required.' }
        return [DateTimeOffset]$Value
    }
    if ($Value -notmatch '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$') {
        throw 'Use an ISO 8601 time with seconds and a timezone.'
    }
    return [DateTimeOffset]::ParseExact(
        $Value, "yyyy-MM-dd'T'HH:mm:ssK",
        [Globalization.CultureInfo]::InvariantCulture
    )
}

$endTime = ConvertTo-LogTime $End
$startTime = $endTime.AddSeconds(-$WindowSeconds)
$lineNumber = 0
$jsonOptions = @{}
if ((Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')) {
    $jsonOptions.DateKind = 'String'
}
$window = @(Get-Content -LiteralPath $Path -Encoding UTF8 | ForEach-Object {
    $lineNumber++
    try {
        $row = $_ | ConvertFrom-Json @jsonOptions
        if ($null -eq $row -or $row -is [array]) { throw 'Expected a JSON object.' }
        $time = ConvertTo-LogTime $row.time
        if (($row.status -isnot [int] -and $row.status -isnot [long]) -or
            $row.status -lt 100 -or $row.status -gt 599) {
            throw 'status must be an integer from 100 to 599.'
        }
        if (($row.request_time_ms -isnot [int] -and
             $row.request_time_ms -isnot [long] -and
             $row.request_time_ms -isnot [double] -and
             $row.request_time_ms -isnot [decimal]) -or
            $row.request_time_ms -lt 0 -or
            [double]::IsNaN([double]$row.request_time_ms) -or
            [double]::IsInfinity([double]$row.request_time_ms)) {
            throw 'request_time_ms must be a finite nonnegative number.'
        }
        foreach ($field in @('method', 'path', 'request_id')) {
            if ($row.$field -isnot [string] -or [string]::IsNullOrWhiteSpace($row.$field)) {
                throw "Missing or invalid field: $field"
            }
        }
        if ($time -ge $startTime -and $time -lt $endTime) { $row }
    }
    catch { throw "Invalid log at line ${lineNumber}: $($_.Exception.Message)" }
})

$count = $window.Count
$errors = @($window | Where-Object { $_.status -ge 500 }).Count
$slow = @($window | Where-Object { $_.request_time_ms -ge 1000 }).Count
$rate = $null
$p95 = $null
$state = 'NO_DATA'
if ($count -gt 0) {
    $rate = 100.0 * $errors / $count
    $times = @($window | ForEach-Object { $_.request_time_ms } | Sort-Object)
    $p95 = $times[[int][Math]::Ceiling(0.95 * $count) - 1]
    $state = 'LOW_TRAFFIC'
    if ($count -ge 10) {
        $state = 'OK'
        if ($rate -ge 20 -or $slow -ge 3) { $state = 'ALERT' }
    }
}

[PSCustomObject]@{
    Start = $startTime.ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    End = $endTime.ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    Requests = $count
    ServerErrors = $errors
    ErrorRatePercent = $(if ($null -ne $rate) { [Math]::Round($rate, 2) } else { $null })
    SlowRequests = $slow
    P95Ms = $p95
    State = $state
}
