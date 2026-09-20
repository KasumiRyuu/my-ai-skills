---
name: safe-autonomous-ops
description: 自主安全操作规范。仅在你显式点名后启用：用于项目工作区内的文件管理、数据处理、脚本运行等免 sudo 任务。允许 cp/mv/mkdir/python3/git 等命令自主执行，但任何导致原内容不可恢复的操作，都必须先建立可回滚点（.trash 备份或工作区快照）。本技能不改变宿主审批策略。
disable-model-invocation: true
---

# 自主安全操作（Safe Autonomous Ops）

## 定位与不承诺的事

- 本技能**不能改变宿主审批策略**。审批由权限档位（`/permissions`）与持久化前缀规则控制。
- 若宿主仍弹出确认，属正常行为，不是本技能失效。想减少弹窗，请在宿主的权限设置里为「建议持久化的前缀规则」一节列出的命令建立持久化放行规则。
- 本技能只负责一件事：**让每一次破坏性操作都可回滚**。

## 可自主执行的范围

仅限当前项目工作区内、无需 sudo 的命令：文件操作、文本查看、`python3`、项目内脚本、git 只读子命令等。

- 允许裸 `python3`：因此**不得**依赖命令白名单来保证安全，安全由下文的回滚点铁律保证。
- 被 `python3` 执行的脚本，只允许写工作区内。若脚本需要写工作区外路径，先停下来报告用户。

## 不可恢复操作清单

定义：**任何导致原内容不可恢复的操作**。命中任一条，必须先建立回滚点：

- 删除类：`rm` `rmdir` `unlink` `shred` `find -delete` `rsync --delete`
- git 破坏类：`git reset --hard` `git clean -fd` `git checkout -- <path>` `git restore <path>`
- 覆盖类：`>` 覆盖已有文件、`truncate`、`sed -i`、`mv` 覆盖已存在的目标
- 间接类：脚本内部的删除或覆写调用（`os.remove`、`shutil.rmtree`、`open(f,'w')` 等）

`sudo`、系统级修改（`apt`/`systemctl`/`reboot`）、`/etc` `/usr` `/opt` `/var` 写入、`dd` `mkfs` 一律禁止，不在回滚点豁免范围内。

## 回滚点铁律

**单目标操作**（一个文件或目录的删除/覆盖/移动）：先把它送进回收站，再对目标做动作。

```bash
TS=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p .trash/$TS/<原目录结构>
mv <目标> .trash/$TS/<相对路径>
```

**批量或高危操作**（`git reset --hard`、`git clean`、批量覆盖、执行会写文件的数据处理脚本）：先做工作区级快照。

```bash
TS=$(date -u +%Y%m%dT%H%M%SZ)
tar -czf .trash/$TS/workspace-snapshot.tar.gz --exclude=.trash .
```

**恢复**：从 `.trash/<时间戳>/` 对应路径移回即可；快照用 `tar -xzf` 解回工作区根。

## 回收站约定

- 位置：工作区根下的 `.trash/<UTC 时间戳>/`，保留原相对路径结构。
- git 项目需把 `.trash/` 加入 `.gitignore`。
- 阈值：`.trash/` 超过 2GB 或 50 份时提示用户，并给出手动清理命令；**绝不代为删除**。
- 快照前先 `du -sh .trash` 确认磁盘余量；大目录项目应按需排除数据目录。

## 建议持久化的前缀规则

读类 + 安全写类可放行；`git` 仅只读子命令放行，`git add/commit` 保持询问，`reset/clean/checkout/restore` 永远询问。

- 只读检索：`rg` `find` `cat` `head` `tail` `sed -n` `grep` `wc` `ls` `pwd`
- git 只读：`git status` `git log` `git diff` `git show`
- 安全写：`cp` `mv` `mkdir` `touch` `tar -czf`

## 边界行为

- 超出范围 → 停下并报告，不擅自执行。
- 需要 sudo → 报告用户手动执行。
- 用户口头说「可以删」→ 默认仍走 `.trash`；仅当用户明确指示「使用 rm」时才允许直接删除。
- 磁盘空间不足需要物理删除 → 报告用户，等待明确指示。
