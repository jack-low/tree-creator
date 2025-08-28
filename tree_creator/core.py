"""
Tree Structure Creator - Create directory and file structures from tree-like text representations.

This module provides functionality to parse tree-like text representations (similar to the output
of the Unix 'tree' command) and create the corresponding directory and file structure on disk.

Fixed version with improved regex parsing and better error handling.
"""

import re
import logging
import argparse
import webbrowser
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Union

# Version info
try:
    from ._version import __version__
except ImportError:
    __version__ = "1.1.3"


class EntryType(Enum):
    FILE = "file"
    DIRECTORY = "directory"


@dataclass
class TreeEntry:
    name: str
    entry_type: EntryType
    depth: int
    path: Optional[Path] = None


class TreeParseError(Exception):
    """Raised when tree parsing fails."""


class TreeCreationError(Exception):
    """Raised when file/directory creation fails."""


class TreeCreator:
    # 最大深度制限
    MAX_DEPTH = 50
    MAX_NAME_LENGTH = 255
    MAX_PATH_LENGTH = 4096

    def __init__(
        self, logger: Optional[logging.Logger] = None, default_encoding: str = "utf-8"
    ):
        self.logger = logger or self._create_default_logger()
        self.default_encoding = default_encoding
        self._stats = {"dirs_created": 0, "files_created": 0}

    def _create_default_logger(self) -> logging.Logger:
        logger = logging.getLogger("TreeCreator")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            logger.addHandler(handler)
        return logger

    def create_from_text(
        self, tree_text: str, base_dir: Union[str, Path] = ".", dry_run: bool = False
    ) -> Dict[str, int]:
        """テキストからツリー構造を作成"""
        self._reset_stats()
        base_path = Path(base_dir).resolve()

        # パス長制限チェック
        if len(str(base_path)) > self.MAX_PATH_LENGTH - 100:  # 余裕を持たせる
            raise TreeCreationError(
                f"Base path too long: {len(str(base_path))} > {self.MAX_PATH_LENGTH - 100}"
            )

        try:
            entries = self._parse_tree(tree_text)
            self._create_structure(entries, base_path, dry_run)
        except Exception as e:
            self.logger.error(f"Failed to create tree structure: {e}")
            raise

        if dry_run:
            self.logger.info(
                f"Dry run completed. Would create: "
                f"{self._stats['dirs_created']} directories, "
                f"{self._stats['files_created']} files"
            )
        else:
            self.logger.info(
                f"Created structure in '{base_path}': "
                f"{self._stats['dirs_created']} directories, "
                f"{self._stats['files_created']} files"
            )

        return self._stats.copy()

    def create_from_file(
        self,
        file_path: Union[str, Path],
        base_dir: Union[str, Path] = ".",
        encoding: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, int]:
        """ファイルからツリー構造を作成"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Tree file not found: {file_path}")

        try:
            text = file_path.read_text(encoding=encoding or self.default_encoding)
        except UnicodeDecodeError as e:
            raise TreeParseError(
                f"Failed to read file with encoding {encoding or self.default_encoding}: {e}"
            )

        self.logger.info(f"Reading tree structure from: {file_path}")
        return self.create_from_text(text, base_dir, dry_run)

    def _parse_tree(self, tree_text: str) -> List[TreeEntry]:
        """改良されたツリー解析"""
        if not tree_text.strip():
            raise TreeParseError("Empty tree text")

        lines = [line.rstrip() for line in tree_text.splitlines()]
        # 空行を除外
        non_empty_lines = [line for line in lines if line.strip()]

        if not non_empty_lines:
            raise TreeParseError("No valid lines found in tree text")

        entries: List[TreeEntry] = []

        for line_idx, line in enumerate(non_empty_lines):
            try:
                entry = self._parse_line_improved(line, line_idx)
                if entry:
                    # 深度制限チェック
                    if entry.depth > self.MAX_DEPTH:
                        raise TreeParseError(
                            f"Maximum depth exceeded: {entry.depth} > {self.MAX_DEPTH}"
                        )

                    # 名前長制限チェック
                    if len(entry.name) > self.MAX_NAME_LENGTH:
                        raise TreeParseError(
                            f"Name too long: '{entry.name[:50]}...' ({len(entry.name)} > {self.MAX_NAME_LENGTH})"
                        )

                    entries.append(entry)

            except Exception as e:
                raise TreeParseError(
                    f"Failed to parse line {line_idx + 1}: '{line}' - {e}"
                )

        if not entries:
            raise TreeParseError("No valid entries found")

        return entries

    def _parse_line_improved(self, line: str, line_idx: int) -> Optional[TreeEntry]:
        """行解析（罫線/スペース混在に対応）"""
        original_line = line

        # コメント除去
        if "#" in line:
            comment_pos = line.find("#")
            line = line[:comment_pos].rstrip()

        if not line.strip():
            return None

        # パターン1: ルートレベル（先頭に罫線/スペースが来ない）
        if not line.startswith(" "):
            name = line.strip()
            depth = 0

        # パターン2: 定型の枝
        elif line.startswith(" ├─ ") or line.startswith(" └─ "):
            name = line[4:].strip()
            depth = 1

        elif line.startswith(" │   ├─ ") or line.startswith(" │   └─ "):
            name = line[8:].strip()
            depth = 2

        else:
            # フォールバック: インデント部分 + 名前
            # ★ 修正点: 正規表現をきちんと閉じ、行末までを対象にする
            match = re.match(r"^(\s*[│├└─\s]*)(.+)$", line, re.UNICODE)
            if not match:
                self.logger.warning(f"Could not parse line: '{original_line}'")
                return None

            indent_str = match.group(1)
            name = match.group(2).strip()

            # おおよその深度（4文字単位程度で増加）を算出
            if len(indent_str) == 0:
                depth = 0
            elif len(indent_str) <= 4:
                depth = 1
            elif len(indent_str) <= 8:
                depth = 2
            else:
                depth = max(0, len(indent_str) // 4)

        if not name:
            return None

        # エントリタイプ判定
        if name.endswith("/"):
            entry_type = EntryType.DIRECTORY
            name = name.rstrip("/")
        else:
            entry_type = EntryType.FILE

        # 無効な文字チェック（Windows 互換）
        invalid_chars = set(name) & set('<>:"|?*\x00')
        if invalid_chars:
            raise TreeParseError(
                f"Invalid characters in name '{name}': {invalid_chars}"
            )

        return TreeEntry(name=name, entry_type=entry_type, depth=depth)

    def _create_structure(
        self, entries: List[TreeEntry], base_path: Path, dry_run: bool
    ):
        """ツリー構造の作成"""
        path_stack: List[str] = []

        for entry in entries:
            try:
                # パススタックを調整
                path_stack = path_stack[: entry.depth]

                # 親ディレクトリパス
                parent_path = (
                    base_path.joinpath(*path_stack) if path_stack else base_path
                )

                # フルパス
                full_path = parent_path / entry.name
                entry.path = full_path

                # パス長制限チェック
                if len(str(full_path)) > self.MAX_PATH_LENGTH:
                    raise TreeCreationError(
                        f"Path too long: {len(str(full_path))} > {self.MAX_PATH_LENGTH}"
                    )

                if entry.entry_type == EntryType.DIRECTORY:
                    self._make_dir(full_path, dry_run)
                    path_stack.append(entry.name)
                else:
                    self._make_file(full_path, parent_path, dry_run)

            except Exception as e:
                raise TreeCreationError(f"Failed to create '{entry.name}': {e}")

    def _make_dir(self, path: Path, dry_run: bool):
        """ディレクトリ作成"""
        if dry_run:
            self.logger.debug(f"Would create directory: {path}")
        else:
            try:
                path.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Created directory: {path}")
            except Exception as e:
                raise TreeCreationError(f"Failed to create directory '{path}': {e}")

        self._stats["dirs_created"] += 1

    def _make_file(self, file_path: Path, parent_path: Path, dry_run: bool):
        """ファイル作成"""
        if dry_run:
            self.logger.debug(f"Would create file: {file_path}")
        else:
            try:
                parent_path.mkdir(parents=True, exist_ok=True)
                file_path.touch(exist_ok=True)
                self.logger.debug(f"Created file: {file_path}")
            except Exception as e:
                raise TreeCreationError(f"Failed to create file '{file_path}': {e}")

        self._stats["files_created"] += 1

    def _reset_stats(self):
        """統計リセット"""
        self._stats = {"dirs_created": 0, "files_created": 0}


# 便利関数
def create_from_text(
    tree_text: str,
    base_dir: Union[str, Path] = ".",
    dry_run: bool = False,
    logger: Optional[logging.Logger] = None,
) -> Dict[str, int]:
    """テキストからツリー構造を作成する便利関数"""
    return TreeCreator(logger).create_from_text(tree_text, base_dir, dry_run)


def create_from_file(
    file_path: Union[str, Path],
    base_dir: Union[str, Path] = ".",
    encoding: str = "utf-8",
    dry_run: bool = False,
    logger: Optional[logging.Logger] = None,
) -> Dict[str, int]:
    """ファイルからツリー構造を作成する便利関数"""
    return TreeCreator(logger).create_from_file(file_path, base_dir, encoding, dry_run)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        prog="tree-creator",
        description="Create directory and file structures from tree-like text representations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example tree file (tree.txt):
    project/
    ├── src/
    │   ├── main.py
    │   └── utils.py
    └── README.md

Usage:
    python tree_creator.py tree.txt --base-dir ./my_project
    tree-creator tree.txt --dry-run
    echo "dir/\\n└── file.txt" | tree-creator -
    tree-creator -b ./output-dir - <<EOF
    myapp/
    ├── index.html
    └── static/
        └── style.css
    EOF
""",
    )

    parser.add_argument(
        "input",
        nargs="?",
        default=None,
        help='Input tree file path (use "-" for stdin, required)',
    )
    parser.add_argument(
        "-b",
        "--base-dir",
        default=".",
        help="Base directory for structure creation (default: current directory)",
    )
    parser.add_argument(
        "-e", "--encoding", default="utf-8", help="Input file encoding (default: utf-8)"
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Simulate creation without actual file operations",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"tree-creator {__version__}"
    )
    parser.add_argument(
        "-I",
        "--issues",
        action="store_true",
        help="Open the project's GitHub issues page",
    )

    args = parser.parse_args()

    if args.issues:
        webbrowser.open("https://github.com/jack-low/tree-creator/issues")
        return 0

    # ログレベル設定
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )

    try:
        creator = TreeCreator()

        if args.input is None:
            print("tree-creator: Create directory structures from tree-like text")
            print("\nUsage examples:")
            print("  tree-creator tree.txt                    # Create from file")
            print("  tree-creator -d tree.txt                 # Dry run")
            print("  echo 'dir/\\n└── file.txt' | tree-creator -  # From stdin")
            print("  tree-creator --help                      # Show full help")
            return 1
        elif args.input == "-":
            import sys

            tree_text = sys.stdin.read()
            if not tree_text.strip():
                logging.error("No input provided from stdin")
                return 1
            stats = creator.create_from_text(tree_text, args.base_dir, args.dry_run)
        else:
            stats = creator.create_from_file(
                args.input, args.base_dir, args.encoding, args.dry_run
            )

        action = "would be " if args.dry_run else ""
        print(
            f"\nSummary: {stats['dirs_created']} directories, "
            f"{stats['files_created']} files {action}created."
        )
        return 0

    except KeyboardInterrupt:
        logging.info("Operation cancelled by user")
        return 130
    except Exception as e:
        logging.error(f"Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
