# PowerShell 回滚操作示例

适用于 Windows PowerShell 5.1 和 PowerShell 7。先完成 `SKILL.md` 中的授权、绝对路径边界、重解析点和并发写入检查，再运行下列示例。所有示例共用前一节生成的变量；不同任务重新设置工作区。

## 1. 确定工作区并创建唯一回滚目录

下面路径仅用于展示，必须替换为本次任务明确授权的工作区。

```powershell
$ErrorActionPreference = 'Stop'
$workspaceRoot = (Resolve-Path -LiteralPath 'C:\Projects\MyProject' -ErrorAction Stop).ProviderPath
$rootItem = Get-Item -LiteralPath $workspaceRoot -Force
if (-not $rootItem.PSIsContainer -or $rootItem.PSProvider.Name -ne 'FileSystem') {
    throw '工作区必须是文件系统目录。'
}
$workspaceRoot = $rootItem.FullName.TrimEnd([char]'\')
$volumeRoot = [System.IO.Path]::GetPathRoot($workspaceRoot)
if ($workspaceRoot.TrimEnd([char]'\') -eq $volumeRoot.TrimEnd([char]'\')) {
    throw '不能把整个磁盘根目录作为默认工作区。'
}
$rootPrefix = $workspaceRoot + '\'
# 路径中的目录联接可能改变实际位置；检查工作区及其祖先。
for ($ancestor = $rootItem; $null -ne $ancestor; $ancestor = $ancestor.Parent) {
    if ($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw '工作区路径含重解析点，需要先确认实际边界。'
    }
}
$trashRoot = Join-Path $workspaceRoot '.trash'
if (Test-Path -LiteralPath $trashRoot) {
    $trashItem = Get-Item -LiteralPath $trashRoot -Force
    if (-not $trashItem.PSIsContainer -or ($trashItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw '.trash 必须是工作区内的普通目录。'
    }
}
$rollbackId = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
$rollbackDir = Join-Path $trashRoot $rollbackId
New-Item -ItemType Directory -Path $rollbackDir -ErrorAction Stop | Out-Null
```

## 2. 查看目标卷的可用空间

```powershell
Get-PSDrive -PSProvider FileSystem |
    Select-Object Name, Root, Used, Free
$driveInfo = [System.IO.DriveInfo]::new($volumeRoot)
[pscustomobject]@{
    Volume = $volumeRoot
    AvailableBytes = $driveInfo.AvailableFreeSpace
}
```

`AvailableFreeSpace` 适用于这里的本地卷示例。若目标为无法查询容量的共享位置，不以其他磁盘的剩余空间代替。备份前用已检查且不跟随重解析点的文件清单计算总大小，并为验证和恢复暂存预留空间。

## 3. 备份即将覆盖的单个文件

下面只备份，不执行覆盖或删除。替换 `data\input.csv` 为实际目标；路径支持空格、中文及方括号。

```powershell
$targetPath = (Resolve-Path -LiteralPath (Join-Path $workspaceRoot 'data\input.csv') -ErrorAction Stop).ProviderPath
$targetPath = [IO.Path]::GetFullPath($targetPath)
if (-not $targetPath.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw '目标不在工作区内部。'
}
$relativePath = $targetPath.Substring($rootPrefix.Length)
if ($relativePath -match '^(?i)\.trash(?:\\|$)' -or $relativePath.Contains(':')) {
    throw '不能把备份目录或备用数据流作为普通文件目标。'
}
$targetItem = Get-Item -LiteralPath $targetPath -Force
if ($targetItem.PSIsContainer) { throw '本示例只处理单个文件。' }
for ($node = $targetItem; $null -ne $node;) {
    if ($node.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw '目标或祖先含重解析点。'
    }
    if ($node.PSIsContainer) { $node = $node.Parent } else { $node = $node.Directory }
}
$backupPath = Join-Path (Join-Path $rollbackDir 'files') $relativePath
New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($backupPath)) -Force | Out-Null
if (Test-Path -LiteralPath $backupPath) { throw '备份目标已存在，不能覆盖。' }
$originalHash = (Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash
$originalLength = $targetItem.Length
Copy-Item -LiteralPath $targetPath -Destination $backupPath -ErrorAction Stop
$backupHash = (Get-FileHash -LiteralPath $backupPath -Algorithm SHA256).Hash
$currentHash = (Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash
$backupLength = (Get-Item -LiteralPath $backupPath -Force).Length
if ($originalHash -ne $backupHash -or $originalHash -ne $currentHash -or $originalLength -ne $backupLength) {
    throw '文件备份不一致或源文件正在变化，不能继续覆盖。'
}
$record = [ordered]@{
    Workspace = $workspaceRoot
    RelativePath = $relativePath
    BackupPath = $backupPath
    SHA256 = $backupHash
    Length = $backupLength
    Operation = 'backup-before-overwrite'
}
$record | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $rollbackDir 'record.json') -Encoding UTF8
```

删除文件或目录时，在同样的检查后使用 `Move-Item -LiteralPath` 移入一个不存在的备份目标，不加 `-Force`。目录需要先枚举并检查全部子项，验证移动后的清单；不要直接复用上面的单文件哈希检查当作目录验证。

## 4. 批量修改前的工作区快照

先停止会写工作区的进程，检查待归档文件和子目录；遇到重解析点或无法读取的项目停止。禁止自行排除可能受操作影响的数据目录。此示例要求已安装 `tar.exe`，可用 `Get-Command tar.exe` 检查；缺失时选用经验证的其他方案，不自行安装软件。

```powershell
$tarCommand = Get-Command tar.exe -ErrorAction Stop
$snapshotPath = Join-Path $rollbackDir 'workspace-snapshot.tar.gz'
if (Test-Path -LiteralPath $snapshotPath) { throw '快照文件已存在。' }
& $tarCommand.Source -czf $snapshotPath --exclude='./.trash' -C $workspaceRoot .
if ($LASTEXITCODE -ne 0) { throw '快照创建失败。' }
& $tarCommand.Source -tzf $snapshotPath
if ($LASTEXITCODE -ne 0) { throw '快照目录校验失败。' }
Get-FileHash -LiteralPath $snapshotPath -Algorithm SHA256
```

目录列表和压缩包哈希只能证明文件可读，不能单独证明源内容已完整保存。对高危操作，把自己刚生成的归档解到空验证目录，与快照前记录的相对路径、长度和 SHA-256 清单比对；排除 `.trash`，包含隐藏文件和空目录。空间不足以完成验证时，不声称回滚点已验证。

不默认使用 `Compress-Archive` 做完整工作区备份，因为它会跳过隐藏文件和目录，参见
[Microsoft 官方说明](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.archive/compress-archive)。
tar 示例也不是系统镜像，不保证 NTFS 权限和特殊元数据恢复。

## 5. 恢复

单文件恢复：先确认记录中的路径仍在本次工作区内，验证备份哈希，并保护当前版本。当前目标不存在时再复制；不要用 `-Force` 跳过冲突检查。

```powershell
# $backupPath 和 $targetPath 来自已核对的回滚记录。
if (Test-Path -LiteralPath $targetPath) {
    throw '先为当前版本建立新的回滚点，再处理目标冲突。'
}
Copy-Item -LiteralPath $backupPath -Destination $targetPath -ErrorAction Stop
if ((Get-FileHash -LiteralPath $backupPath -Algorithm SHA256).Hash -ne
    (Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash) {
    throw '恢复后的文件内容不一致。'
}
```

快照恢复：只使用来源和哈希已确认的自身归档。先查看成员，拒绝绝对路径、`..` 越界成员和未确认的链接，再解到新的空暂存目录。核对内容后逐项恢复；对快照之后新增的文件单独确认并送入新回滚点。恢复 `.git` 前关闭占用它的进程，单独确认 Git 元数据恢复方案。完成后运行与任务相关的检查，并保留原回滚点。
