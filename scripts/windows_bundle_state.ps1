#Requires -Version 5.1

$script:OmnigentBundleReceiptName = ".omnigent-bundle-receipt.json"
$script:OmnigentBundleProduct = "omnigent-windows-bundle"

function Test-OmnigentPathEqualOrBeneath([string]$Path, [string]$Root) {
    $comparison = [System.StringComparison]::OrdinalIgnoreCase
    if ([string]::Equals($Path.TrimEnd('\'), $Root.TrimEnd('\'), $comparison)) {
        return $true
    }
    $rootWithSeparator = $Root.TrimEnd('\') + '\'
    return $Path.StartsWith($rootWithSeparator, $comparison)
}

function Get-OmnigentCanonicalEnvironmentPath([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return $null }
    try {
        $fullPath = [System.IO.Path]::GetFullPath($Path)
    } catch {
        return $null
    }
    if ($fullPath -notmatch '^[A-Za-z]:\\') { return $null }
    if ([string]::Equals($fullPath, [System.IO.Path]::GetPathRoot($fullPath), [System.StringComparison]::OrdinalIgnoreCase)) {
        return $fullPath
    }
    return $fullPath.TrimEnd('\')
}

function Assert-OmnigentSafePathComponent([string]$Component, [string]$Context) {
    if ([string]::IsNullOrEmpty($Component) -or $Component -eq '.' -or $Component -eq '..' -or
        $Component -match '[\x00-\x1F<>:"/\\|?*\[\]]' -or $Component -match '[. ]$' -or
        $Component -match '^(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$') {
        throw "$Context contains an unsafe Windows path component: $Component"
    }
}

function Assert-OmnigentNoReparseAncestors([string]$Path) {
    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $root = [System.IO.Path]::GetPathRoot($fullPath)
    if ([string]::IsNullOrWhiteSpace($root) -or $root -notmatch '^[A-Za-z]:\\$') {
        throw "The bundle prefix must be on a local filesystem drive: $Path"
    }

    $drive = New-Object System.IO.DriveInfo($root)
    if (-not $drive.IsReady -or $drive.DriveType -eq [System.IO.DriveType]::Network) {
        throw "The bundle prefix drive is unavailable or not local: $root"
    }
    $rootItem = Get-Item -LiteralPath $root -Force -ErrorAction Stop
    if (($rootItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "The bundle prefix drive root is a reparse point: $root"
    }

    $current = $root
    $relative = $fullPath.Substring($root.Length)
    foreach ($part in @($relative -split '\\' | Where-Object { $_ })) {
        $current = Join-Path $current $part
        try {
            $item = Get-Item -LiteralPath $current -Force -ErrorAction Stop
        } catch {
            if ($_.CategoryInfo.Category -eq [System.Management.Automation.ErrorCategory]::ObjectNotFound) { break }
            throw
        }
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "The bundle prefix path contains a reparse point: $current"
        }
        if ($current -ne $fullPath -and -not $item.PSIsContainer) {
            throw "A bundle prefix ancestor is not a directory: $current"
        }
    }
}

function Resolve-OmnigentBundlePrefix([string]$InstallDir) {
    if ([string]::IsNullOrWhiteSpace($InstallDir)) {
        throw "InstallDir must be a non-empty absolute local filesystem path."
    }
    $candidate = $InstallDir
    if ($candidate.StartsWith('-') -or $candidate -match '[\x00-\x1F<>"|*?\[\]]' -or $candidate -match ':.*:') {
        throw "InstallDir contains an option, wildcard, or alternate-stream marker."
    }
    if ($candidate -match '^[\\/]{2}' -or $candidate -match '^\\\\\?\\' -or $candidate -match '^\\\\\.\\') {
        throw "UNC and device paths are not valid bundle prefixes."
    }
    if ($candidate -notmatch '^[A-Za-z]:[\\/]') {
        throw "InstallDir must be an absolute drive path, not a relative, drive-relative, or provider path."
    }
    if ($candidate.Substring(2) -match ':') {
        throw "Alternate data streams are not valid bundle prefixes."
    }

    $normalizedInput = $candidate.Replace('/', '\')
    foreach ($part in @($normalizedInput.Substring(3) -split '\\' | Where-Object { $_ })) {
        Assert-OmnigentSafePathComponent $part 'InstallDir'
    }
    try {
        $fullPath = [System.IO.Path]::GetFullPath($normalizedInput)
    } catch {
        throw "InstallDir is not a valid filesystem path: $InstallDir"
    }
    if ($fullPath -notmatch '^[A-Za-z]:\\') {
        throw "InstallDir must resolve to a local drive path."
    }
    $driveRoot = [System.IO.Path]::GetPathRoot($fullPath)
    if ([string]::Equals($fullPath.TrimEnd('\'), $driveRoot.TrimEnd('\'), [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "A filesystem drive root cannot be used as the bundle prefix."
    }
    $prefix = $fullPath.TrimEnd('\')

    $userPrograms = if ($env:LOCALAPPDATA) { Join-Path $env:LOCALAPPDATA 'Programs' } else { $null }
    $protectedRoots = @(
        $env:USERPROFILE,
        $env:LOCALAPPDATA,
        $userPrograms,
        $env:APPDATA,
        $env:ProgramFiles,
        ${env:ProgramFiles(x86)},
        $env:ProgramData,
        [System.IO.Path]::GetTempPath(),
        [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Windows),
        $env:SystemRoot,
        $env:WINDIR
    )
    foreach ($protected in $protectedRoots) {
        $protectedPath = Get-OmnigentCanonicalEnvironmentPath $protected
        if (-not $protectedPath) { continue }
        if (Test-OmnigentPathEqualOrBeneath $protectedPath $prefix) {
            throw "InstallDir is equal to or an ancestor of a protected location: $protectedPath"
        }
    }

    $windowsRoots = @(
        [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Windows),
        $env:SystemRoot,
        $env:WINDIR
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    foreach ($windowsRoot in $windowsRoots) {
        $windowsPath = Get-OmnigentCanonicalEnvironmentPath $windowsRoot
        if ($windowsPath -and (Test-OmnigentPathEqualOrBeneath $prefix $windowsPath)) {
            throw "InstallDir cannot be within the Windows or system directory tree: $windowsPath"
        }
    }
    $windowsRoot = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Windows)
    if (-not [string]::IsNullOrWhiteSpace($windowsRoot)) {
        $system32Path = Get-OmnigentCanonicalEnvironmentPath (Join-Path $windowsRoot 'System32')
        if ($system32Path -and (Test-OmnigentPathEqualOrBeneath $prefix $system32Path)) {
            throw "InstallDir cannot be within the Windows or system directory tree: $system32Path"
        }
    }

    Assert-OmnigentNoReparseAncestors $prefix
    $prefixItem = Get-Item -LiteralPath $prefix -Force -ErrorAction SilentlyContinue
    if ($null -ne $prefixItem -and -not $prefixItem.PSIsContainer) {
        throw "InstallDir exists as a file, not a directory: $prefix"
    }
    return $prefix
}

function Get-OmnigentReceiptPath([string]$Prefix) {
    return Join-Path $Prefix $script:OmnigentBundleReceiptName
}

function Read-OmnigentBundleReceipt([string]$Prefix) {
    $receiptPath = Get-OmnigentReceiptPath $Prefix
    Assert-OmnigentNoReparseAncestors $receiptPath
    $receiptItem = Get-Item -LiteralPath $receiptPath -Force -ErrorAction SilentlyContinue
    if ($null -eq $receiptItem) { return $null }
    if ($receiptItem.PSIsContainer -or ($receiptItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "The bundle receipt is not an ordinary file: $receiptPath"
    }
    if ($receiptItem.Length -gt 16MB) { throw "The bundle receipt exceeds the permitted size: $receiptPath" }
    try {
        $receipt = [System.IO.File]::ReadAllText($receiptPath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json -ErrorAction Stop
    } catch {
        throw "The bundle receipt is malformed: $receiptPath"
    }
    if ($null -eq $receipt -or $receipt -isnot [System.Management.Automation.PSCustomObject] -or
        @($receipt.PSObject.Properties | ForEach-Object { $_.Name } | Where-Object { $_ -cnotin @('schema_version', 'product', 'prefix', 'inventory') }).Count -gt 0 -or
        @($receipt.PSObject.Properties).Count -ne 4 -or
        ($receipt.schema_version -isnot [int] -and $receipt.schema_version -isnot [long]) -or
        $receipt.schema_version -ne 1 -or $receipt.product -cne $script:OmnigentBundleProduct) {
        throw "The bundle receipt has an unsupported schema or product: $receiptPath"
    }
    if ($receipt.prefix -isnot [string] -or -not [string]::Equals($receipt.prefix, $Prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "The bundle receipt is bound to a different install prefix: $receiptPath"
    }
    if ($receipt.inventory -isnot [array] -or $receipt.inventory.Count -eq 0 -or $receipt.inventory.Count -gt 100000) {
        throw "The bundle receipt has no valid inventory: $receiptPath"
    }

    $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    $items = New-Object 'System.Collections.Generic.List[object]'
    foreach ($entry in @($receipt.inventory)) {
        if ($null -eq $entry -or $entry -isnot [System.Management.Automation.PSCustomObject] -or
            @($entry.PSObject.Properties).Count -ne 2 -or
            @($entry.PSObject.Properties | ForEach-Object { $_.Name } | Where-Object { $_ -cnotin @('path', 'kind') }).Count -gt 0 -or
            $entry.path -isnot [string] -or [string]::IsNullOrEmpty($entry.path) -or $entry.kind -isnot [string]) {
            throw "The bundle receipt contains an invalid inventory entry."
        }
        $relative = $entry.path
        $kind = $entry.kind
        if ($relative.Contains('\') -or $relative.StartsWith('/') -or $relative -match '[:*?\[\]]' -or
            $relative -match '(^|/)\.\.?(/|$)' -or $relative -match '//') {
            throw "The bundle receipt contains an unsafe inventory path: $relative"
        }
        $parts = @($relative -split '/')
        foreach ($part in $parts) { Assert-OmnigentSafePathComponent $part 'The bundle receipt' }
        if ((-not [string]::Equals($parts[0], 'tools', [System.StringComparison]::OrdinalIgnoreCase) -and
             -not [string]::Equals($parts[0], 'bin', [System.StringComparison]::OrdinalIgnoreCase)) -or
            @($parts | Where-Object { [string]::IsNullOrEmpty($_) }).Count -gt 0 -or
            ($kind -cne 'file' -and $kind -cne 'directory')) {
            throw "The bundle receipt contains an unsupported inventory entry: $relative"
        }
        if (-not $seen.Add($relative)) {
            throw "The bundle receipt contains a duplicate inventory path: $relative"
        }
        if (($parts.Count -eq 1) -and $kind -cne 'directory') {
            throw "The bundle receipt root entry must be a directory: $relative"
        }
        $items.Add([pscustomobject]@{ Path = $relative; Kind = $kind })
    }
    $itemsByPath = @{}
    foreach ($item in $items) { $itemsByPath[$item.Path] = $item }
    foreach ($requiredRoot in @('tools', 'bin')) {
        if (-not $itemsByPath.ContainsKey($requiredRoot) -or $itemsByPath[$requiredRoot].Kind -cne 'directory') {
            throw "The bundle receipt is missing its expected directory: $requiredRoot"
        }
    }
    foreach ($entry in $items) {
        $parts = @($entry.Path -split '/')
        for ($index = 1; $index -lt $parts.Count; $index++) {
            $parentPath = ($parts[0..($index - 1)] -join '/')
            if (-not $itemsByPath.ContainsKey($parentPath) -or $itemsByPath[$parentPath].Kind -cne 'directory') {
                throw "The bundle receipt has a missing or non-directory parent for: $($entry.Path)"
            }
        }
    }
    return [pscustomobject]@{
        schema_version = 1
        product = $script:OmnigentBundleProduct
        prefix = $Prefix
        inventory = $items.ToArray()
    }
}

function Get-OmnigentLiveInventory([string]$Prefix) {
    $inventory = New-Object 'System.Collections.Generic.List[object]'
    $rootEntries = @(Get-ChildItem -LiteralPath $Prefix -Force -ErrorAction Stop)
    foreach ($entry in $rootEntries) {
        if ($entry.Name -ceq $script:OmnigentBundleReceiptName) { continue }
        if (-not [string]::Equals($entry.Name, 'tools', [System.StringComparison]::OrdinalIgnoreCase) -and
            -not [string]::Equals($entry.Name, 'bin', [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Unexpected item in the bundle prefix: $($entry.FullName)"
        }
        if (-not $entry.PSIsContainer) {
            throw "Expected a bundle directory but found a file: $($entry.FullName)"
        }
    }

    $pending = New-Object 'System.Collections.Generic.Stack[System.IO.DirectoryInfo]'
    foreach ($rootName in @('tools', 'bin')) {
        $rootPath = Join-Path $Prefix $rootName
        $rootItem = Get-Item -LiteralPath $rootPath -Force -ErrorAction SilentlyContinue
        if ($null -eq $rootItem) { continue }
        if (($rootItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "A bundle inventory directory is a reparse point: $rootPath"
        }
        if (-not $rootItem.PSIsContainer) { throw "Expected a bundle directory but found a file: $rootPath" }
        $inventory.Add([pscustomobject]@{ Path = $rootName; Kind = 'directory' })
        $pending.Push([System.IO.DirectoryInfo]$rootItem)
    }

    while ($pending.Count -gt 0) {
        $directory = $pending.Pop()
        foreach ($child in @(Get-ChildItem -LiteralPath $directory.FullName -Force -ErrorAction Stop)) {
            if (($child.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "A bundle inventory item is a reparse point: $($child.FullName)"
            }
            $relative = $child.FullName.Substring($Prefix.Length).TrimStart('\').Replace('\', '/')
            if ($child.PSIsContainer) {
                $inventory.Add([pscustomobject]@{ Path = $relative; Kind = 'directory' })
                $pending.Push([System.IO.DirectoryInfo]$child)
            } else {
                if (($child.Attributes -band [System.IO.FileAttributes]::Directory) -ne 0) {
                    throw "A bundle inventory item has an unsupported filesystem type: $($child.FullName)"
                }
                $inventory.Add([pscustomobject]@{ Path = $relative; Kind = 'file' })
            }
        }
    }
    return $inventory.ToArray()
}

function Assert-OmnigentLiveInventoryMatches([string]$Prefix, $Receipt, [switch]$AllowMissing) {
    $live = @(Get-OmnigentLiveInventory $Prefix)
    $expectedByPath = @{}
    foreach ($entry in @($Receipt.inventory)) { $expectedByPath[$entry.Path] = $entry.Kind }
    # Python may cache imports after the receipt is written. Only derive caches
    # from recorded sources in this tool's site-packages, never arbitrary files.
    foreach ($entry in @($Receipt.inventory)) {
        if ($entry.Kind -cne 'file' -or $entry.Path -notmatch '^tools/omnigent/Lib/site-packages/(.*/)?([^/]+)\.py$') {
            continue
        }
        $cacheDirectory = 'tools/omnigent/Lib/site-packages/' + $Matches[1] + '__pycache__'
        $moduleName = $Matches[2]
        if (-not $expectedByPath.ContainsKey($cacheDirectory)) { $expectedByPath[$cacheDirectory] = 'directory' }
        foreach ($optimization in @('', '.opt-1', '.opt-2')) {
            $cachePath = $cacheDirectory + '/' + $moduleName + '.cpython-312' + $optimization + '.pyc'
            if (-not $expectedByPath.ContainsKey($cachePath)) { $expectedByPath[$cachePath] = 'file' }
        }
    }
    $liveByPath = @{}
    foreach ($entry in $live) {
        if (-not $expectedByPath.ContainsKey($entry.Path)) {
            throw "Unexpected item appeared in the owned bundle: $($entry.Path)"
        }
        if ($expectedByPath[$entry.Path] -cne $entry.Kind) {
            throw "An owned bundle item changed type: $($entry.Path)"
        }
        $liveByPath[$entry.Path] = $entry.Kind
    }
    if (-not $AllowMissing) {
        foreach ($entry in @($Receipt.inventory)) {
            if (-not $liveByPath.ContainsKey($entry.Path)) {
                throw "A recorded bundle item is missing: $($entry.Path)"
            }
        }
    }
    return $live
}

function Assert-OmnigentBundleReceiptIsOrdinary([string]$Prefix) {
    $receiptPath = Get-OmnigentReceiptPath $Prefix
    Assert-OmnigentNoReparseAncestors $receiptPath
    $item = Get-Item -LiteralPath $receiptPath -Force -ErrorAction SilentlyContinue
    if ($null -eq $item) {
        throw "The bundle ownership receipt is missing: $receiptPath"
    }
    if ($item.PSIsContainer -or ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "The bundle ownership receipt is not an ordinary file: $receiptPath"
    }
}

function Get-OmnigentBundleState([string]$Prefix, [switch]$ForInstall) {
    $canonicalPrefix = Resolve-OmnigentBundlePrefix $Prefix
    $present = [System.IO.Directory]::Exists($canonicalPrefix)
    $receipt = $null
    if ($present) {
        $rootEntries = @(Get-ChildItem -LiteralPath $canonicalPrefix -Force -ErrorAction Stop)
        $receipt = Read-OmnigentBundleReceipt $canonicalPrefix
        if ($null -eq $receipt) {
            $nonReceiptEntries = @($rootEntries | Where-Object { $_.Name -cne $script:OmnigentBundleReceiptName })
            if ($nonReceiptEntries.Count -gt 0) {
                throw "The non-empty bundle prefix has no valid ownership receipt: $canonicalPrefix"
            }
            if (-not $ForInstall) {
                throw "The bundle prefix has no ownership receipt: $canonicalPrefix"
            }
        } else {
            $null = Assert-OmnigentLiveInventoryMatches $canonicalPrefix $receipt -AllowMissing:(-not $ForInstall.IsPresent)
        }
    } elseif (-not $ForInstall) {
        return [pscustomobject]@{ Prefix = $canonicalPrefix; Present = $false; Receipt = $null }
    }
    return [pscustomobject]@{ Prefix = $canonicalPrefix; Present = $present; Receipt = $receipt }
}

function Write-OmnigentBundleReceipt([string]$Prefix) {
    $canonicalPrefix = Resolve-OmnigentBundlePrefix $Prefix
    if (-not [System.IO.Directory]::Exists($canonicalPrefix)) {
        throw "The bundle prefix does not exist after installation: $canonicalPrefix"
    }
    Assert-OmnigentNoReparseAncestors $canonicalPrefix

    $receiptPath = Get-OmnigentReceiptPath $canonicalPrefix
    $null = Read-OmnigentBundleReceipt $canonicalPrefix
    $inventory = @(Get-OmnigentLiveInventory $canonicalPrefix)
    foreach ($requiredRoot in @('tools', 'bin')) {
        if (@($inventory | Where-Object {
            [string]::Equals($_.Path, $requiredRoot, [System.StringComparison]::OrdinalIgnoreCase) -and $_.Kind -ceq 'directory'
        }).Count -ne 1) {
            throw "The installed bundle is missing its expected directory: $requiredRoot"
        }
    }
    $inventory = @($inventory | Sort-Object -Property Path)
    $receipt = [ordered]@{
        schema_version = 1
        product = $script:OmnigentBundleProduct
        prefix = $canonicalPrefix
        inventory = @($inventory | ForEach-Object { [ordered]@{ path = $_.Path; kind = $_.Kind } })
    }
    $json = ($receipt | ConvertTo-Json -Depth 8) -replace "`r`n", "`n"
    if (-not $json.EndsWith("`n")) { $json += "`n" }
    $encoding = New-Object System.Text.UTF8Encoding($false)
    $temporaryPath = Join-Path $canonicalPrefix ('.' + $script:OmnigentBundleReceiptName + '.' + [Guid]::NewGuid().ToString('N') + '.tmp')
    $stream = $null
    $createdTemporary = $false
    try {
        $stream = New-Object System.IO.FileStream($temporaryPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
        $createdTemporary = $true
        $bytes = $encoding.GetBytes($json)
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
        $stream.Dispose()
        $stream = $null
        Assert-OmnigentNoReparseAncestors $temporaryPath
        $existingReceipt = Get-Item -LiteralPath $receiptPath -Force -ErrorAction SilentlyContinue
        if ($null -ne $existingReceipt) {
            if ($existingReceipt.PSIsContainer -or ($existingReceipt.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "The bundle receipt target is not an ordinary file: $receiptPath"
            }
            [System.IO.File]::Replace($temporaryPath, $receiptPath, [System.Management.Automation.Language.NullString]::Value)
        } else {
            [System.IO.File]::Move($temporaryPath, $receiptPath)
        }
    } finally {
        if ($null -ne $stream) { $stream.Dispose() }
        $temporaryItem = if ($createdTemporary) { Get-Item -LiteralPath $temporaryPath -Force -ErrorAction SilentlyContinue } else { $null }
        if ($null -ne $temporaryItem) {
            Assert-OmnigentNoReparseAncestors $temporaryPath
            if ($temporaryItem.PSIsContainer -or ($temporaryItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Refusing to remove a changed receipt temporary file: $temporaryPath"
            }
            [System.IO.File]::Delete($temporaryPath)
        }
    }
}

function Remove-OmnigentBundleInventory($State) {
    if ($null -eq $State -or -not $State.Present -or $null -eq $State.Receipt) { return }
    $prefix = Resolve-OmnigentBundlePrefix ([string]$State.Prefix)
    if (-not [string]::Equals($prefix, [string]$State.Prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "The bundle state prefix is not canonical."
    }
    $receipt = Read-OmnigentBundleReceipt $prefix
    if ($null -eq $receipt) { throw "The bundle ownership receipt is missing: $prefix" }
    $stateReceipt = $State.Receipt
    if (-not [string]::Equals([string]$stateReceipt.prefix, $prefix, [System.StringComparison]::OrdinalIgnoreCase) -or
        $stateReceipt.schema_version -ne 1 -or $stateReceipt.product -cne $script:OmnigentBundleProduct) {
        throw "The captured bundle state receipt is invalid."
    }
    $capturedByPath = @{}
    foreach ($entry in @($stateReceipt.inventory)) { $capturedByPath[$entry.Path] = $entry.Kind }
    if ($capturedByPath.Count -ne @($stateReceipt.inventory).Count -or $capturedByPath.Count -ne $receipt.inventory.Count) {
        throw "The bundle receipt changed after state was captured; preserving the bundle."
    }
    $receiptByPath = @{}
    foreach ($entry in $receipt.inventory) {
        if (-not $capturedByPath.ContainsKey($entry.Path) -or $capturedByPath[$entry.Path] -cne $entry.Kind) {
            throw "The bundle receipt changed after state was captured; preserving the bundle."
        }
        $receiptByPath[$entry.Path] = $entry.Kind
    }
    foreach ($entry in @($stateReceipt.inventory)) {
        if (-not $receiptByPath.ContainsKey($entry.Path) -or $receiptByPath[$entry.Path] -cne $entry.Kind) {
            throw "The bundle receipt changed after state was captured; preserving the bundle."
        }
    }
    $liveInventory = @(Assert-OmnigentLiveInventoryMatches $prefix $stateReceipt -AllowMissing)
    Assert-OmnigentBundleReceiptIsOrdinary $prefix

    $files = @($liveInventory | Where-Object { $_.Kind -ceq 'file' } | Sort-Object -Property Path)
    foreach ($entry in $files) {
        $path = Join-Path $prefix ($entry.Path.Replace('/', '\'))
        Assert-OmnigentNoReparseAncestors $path
        $item = Get-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
        if ($null -ne $item) {
            if ($item.PSIsContainer -or ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Refusing to remove a changed or reparse bundle file: $path"
            }
            [System.IO.File]::Delete($path)
        }
    }

    Assert-OmnigentLiveInventoryMatches $prefix $receipt -AllowMissing | Out-Null
    Assert-OmnigentBundleReceiptIsOrdinary $prefix
    $directories = @($liveInventory | Where-Object { $_.Kind -ceq 'directory' } |
        Sort-Object { ($_.Path -split '/').Count } -Descending)
    foreach ($entry in $directories) {
        $path = Join-Path $prefix ($entry.Path.Replace('/', '\'))
        Assert-OmnigentNoReparseAncestors $path
        $item = Get-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
        if ($null -ne $item) {
            if (-not $item.PSIsContainer -or ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Refusing to remove a changed or reparse bundle directory: $path"
            }
            [System.IO.Directory]::Delete($path, $false)
        }
    }

    Assert-OmnigentLiveInventoryMatches $prefix $stateReceipt -AllowMissing | Out-Null
    Assert-OmnigentBundleReceiptIsOrdinary $prefix
    $receiptPath = Get-OmnigentReceiptPath $prefix
    Assert-OmnigentNoReparseAncestors $prefix
    $remaining = @(Get-ChildItem -LiteralPath $prefix -Force -ErrorAction Stop)
    if ($remaining.Count -ne 1 -or $remaining[0].Name -cne $script:OmnigentBundleReceiptName) {
        throw "Unexpected items remain in the bundle prefix; preserving the receipt and directory: $prefix"
    }
    Assert-OmnigentBundleReceiptIsOrdinary $prefix
    [System.IO.File]::Delete($receiptPath)
    [System.IO.Directory]::Delete($prefix, $false)
}
