param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$FeedGoArguments
)

$ErrorActionPreference = "Stop"
$runner = Join-Path $PSScriptRoot "feedgo.py"
& python $runner @FeedGoArguments
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
