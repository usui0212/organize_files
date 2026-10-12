from pathlib import Path
import shutil
import click


def move_file(src: Path, dest_dir: Path, label: str) -> bool:
    """ファイルを移動するヘルパー関数（同名ファイルが存在する場合はスキップ）"""
    dest = dest_dir / src.name
    if not dest.exists():
        shutil.move(str(src), str(dest))
        click.echo(f"[{label}] {src.name} -> {dest_dir.name}/")
        return True

    click.echo(f"[スキップ] 移動先に同名ファイルが存在します: {src.name}")
    return False


def organize_by_existing_folders(files: list[Path], folders: list[Path]) -> None:
    """① 既存のフォルダ名に基づいてファイルを移動する"""
    for file_path in files:
        for folder_path in folders:
            # 拡張子を除いたファイル名にフォルダ名が含まれるか判定
            if folder_path.name in file_path.stem:
                move_file(file_path, folder_path, label="移動完了")
                break


def organize_by_user_keywords(
    target_dir: Path,
    remaining_files: list[Path],
    existing_folder_names: set[str],
) -> None:
    """② 未整理ファイルからエディタを開き、手動入力されたキーワードで新規作成・移動する"""
    click.echo(f"\n未整理のファイルが {len(remaining_files)} 件残っています。")

    # エディタに渡す初期テキストを生成（ファイル名の改行区切り）
    initial_content = "\n".join(p.stem for p in remaining_files)
    edited_content = click.edit(initial_content, extension=".txt")

    if not edited_content:
        click.echo("テキストの編集が行われなかったため、処理を中断します。")
        return

    keywords = [
        line.strip() for line in edited_content.splitlines() if line.strip()
    ]
    warnings = []
    created_folders = set()

    for file_path in remaining_files:
        if not file_path.exists():
            continue

        for kw in keywords:
            if kw in file_path.stem:
                # 処理前から存在するフォルダ名と一致する場合は警告を出してスキップ
                if kw in existing_folder_names:
                    warnings.append(
                        f"フォルダ '{kw}' は処理前から存在するため作成をスキップしました (対象: {file_path.name})"
                    )
                else:
                    new_folder = target_dir / kw
                    if kw not in created_folders:
                        new_folder.mkdir(parents=True, exist_ok=True)
                        created_folders.add(kw)

                    move_file(file_path, new_folder, label="新規作成&移動")
                break

    if warnings:
        click.echo("\n================ 警告 ================")
        for w in warnings:
            click.echo(f"[WARNING] {w}")
        click.echo("======================================")


@click.command()
@click.argument(
    "target_dir", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
def main(target_dir: Path):
    """ファイル名に基づいてフォルダ整理を行うメイン処理"""

    # 対象データの取得
    files = [p for p in target_dir.iterdir() if p.is_file()]
    folders = sorted(
        [p for p in target_dir.iterdir() if p.is_dir()],
        key=lambda p: len(p.name),
        reverse=True,
    )
    existing_folder_names = {p.name for p in folders}

    # Step 1: 既存フォルダへの振分け処理
    organize_by_existing_folders(files, folders)

    # Step 2: 残ったファイルの振り分け処理（手動キーワード指定）
    remaining_files = sorted([p for p in target_dir.iterdir() if p.is_file()], key=lambda p: len(p.name), reverse=True)
    if remaining_files:
        organize_by_user_keywords(
            target_dir, remaining_files, existing_folder_names
        )

    click.echo("\n処理が終了しました。")


if __name__ == "__main__":
    main()