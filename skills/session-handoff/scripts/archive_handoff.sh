#!/usr/bin/env bash
# 归档当前的 AGENT_HANDOFF.md，为写一份全新的做准备。
# 用法: bash archive_handoff.sh /path/to/agent-docs
#
# 行为:
#   - 若 agent-docs 目录不存在: 报错退出（应该先初始化项目文档文件夹）
#   - 若目录存在但没有 AGENT_HANDOFF.md: 什么都不做，正常退出（说明是第一次生成）
#   - 若存在 AGENT_HANDOFF.md: 原样移动到 handoff_archive/AGENT_HANDOFF_<timestamp>.md，
#     不修改其内容，只是搬家，为新写一份让路。

set -euo pipefail

DOCS_DIR="${1:-}"

if [[ -z "$DOCS_DIR" ]]; then
  echo "用法: bash archive_handoff.sh /path/to/agent-docs" >&2
  exit 1
fi

if [[ ! -d "$DOCS_DIR" ]]; then
  echo "错误: 目录不存在: $DOCS_DIR" >&2
  echo "请先初始化项目文档文件夹（参照 assets/ 下的模板）再运行此脚本。" >&2
  exit 1
fi

HANDOFF_FILE="$DOCS_DIR/AGENT_HANDOFF.md"
ARCHIVE_DIR="$DOCS_DIR/handoff_archive"

if [[ ! -f "$HANDOFF_FILE" ]]; then
  echo "没有找到现有的 AGENT_HANDOFF.md，跳过归档（这应该是第一次生成交接文档）。"
  exit 0
fi

mkdir -p "$ARCHIVE_DIR"

TIMESTAMP="$(date +%Y-%m-%d_%H%M)"
DEST="$ARCHIVE_DIR/AGENT_HANDOFF_${TIMESTAMP}.md"

# 避免同一分钟内重复运行导致覆盖已归档文件
SUFFIX=1
while [[ -e "$DEST" ]]; do
  DEST="$ARCHIVE_DIR/AGENT_HANDOFF_${TIMESTAMP}_${SUFFIX}.md"
  SUFFIX=$((SUFFIX + 1))
done

mv "$HANDOFF_FILE" "$DEST"
echo "已归档旧的交接文档到: $DEST"
echo "现在可以在 $DOCS_DIR 下写一份全新的 AGENT_HANDOFF.md 了。"
