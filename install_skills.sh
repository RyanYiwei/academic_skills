
set -euo pipefail

DEFAULT_DEST="$HOME/.claude/skills"
SOURCE_DIR="$(pwd)/skills"

read -r -p "复制到哪个 Skills 文件夹？[默认: $DEFAULT_DEST] " DEST_DIR
DEST_DIR="${DEST_DIR:-$DEFAULT_DEST}"

# 手动展开用户输入的 ~
case "$DEST_DIR" in
    "~")
        DEST_DIR="$HOME"
        ;;
    "~/"*)
        DEST_DIR="$HOME/${DEST_DIR#\~/}"
        ;;
esac

mkdir -p "$DEST_DIR"

echo
echo "源目录：$SOURCE_DIR"
echo "目标目录：$DEST_DIR"
echo

found=0
copied=0
skipped=0

for skill_dir in "$SOURCE_DIR"/*/; do
    # 当前目录下没有子文件夹时跳过
    [[ -d "$skill_dir" ]] || continue

    # 只把包含 SKILL.md 的目录视为 Skill
    [[ -f "${skill_dir}SKILL.md" ]] || continue

    found=$((found + 1))

    skill_name="$(basename "$skill_dir")"
    target_path="$DEST_DIR/$skill_name"

    if [[ -e "$target_path" ]]; then
        read -r -p "Skill '$skill_name' 已存在，是否覆盖？[y/N] " answer

        case "$answer" in
            y|Y|yes|YES|Yes)
                rm -rf -- "$target_path"
                ;;
            *)
                echo "跳过：$skill_name"
                skipped=$((skipped + 1))
                continue
                ;;
        esac
    fi

    cp -R -- "$skill_dir" "$target_path"
    echo "已复制：$skill_name"
    copied=$((copied + 1))
done

echo

if [[ "$found" -eq 0 ]]; then
    echo "没有找到包含 SKILL.md 的一级子文件夹。"
    exit 1
fi

echo "完成：复制 $copied 个，跳过 $skipped 个。"