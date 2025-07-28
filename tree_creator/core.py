"""
Tree Structure Creator - Create directory and file structures from tree-like text representations.

This module provides functionality to parse tree-like text representations (similar to the output
of the Unix 'tree' command) and create the corresponding directory and file structure on disk.

Example:
    from tree_creator import TreeCreator

    tree_text = '''
    project/
    ├── src/
    │   ├── main.py
    │   └── utils.py
    └── README.md
    '''

    creator = TreeCreator()
    creator.create_from_text(tree_text, base_dir='./my_project')
"""

import re
import logging
import argparse
import webbrowser
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Union

from ._version import __version__


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
    TREE_CHARS = {
        'vertical': '│',
        'branch': '├──',
        'last': '└──',
    }

    def __init__(self, logger: Optional[logging.Logger] = None, default_encoding: str = 'utf-8'):
        self.logger = logger or self._create_default_logger()
        self.default_encoding = default_encoding
        self._stats = {'dirs_created': 0, 'files_created': 0}

    def _create_default_logger(self) -> logging.Logger:
        logger = logging.getLogger('TreeCreator')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
        return logger

    def create_from_text(self, tree_text: str,
                         base_dir: Union[str, Path] = '.',
                         dry_run: bool = False) -> Dict[str, int]:
        self._reset_stats()
        base_path = Path(base_dir).resolve()

        entries = self._parse_tree(tree_text)
        self._create_structure(entries, base_path, dry_run)

        if dry_run:
            self.logger.info(f"Dry run completed. Would create: "
                             f"{self._stats['dirs_created']} directories, "
                             f"{self._stats['files_created']} files")
        else:
            self.logger.info(f"Created structure in '{base_path}': "
                             f"{self._stats['dirs_created']} directories, "
                             f"{self._stats['files_created']} files")

        return self._stats.copy()

    def create_from_file(self, file_path: Union[str, Path],
                         base_dir: Union[str, Path] = '.',
                         encoding: Optional[str] = None,
                         dry_run: bool = False) -> Dict[str, int]:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Tree file not found: {file_path}")
        text = file_path.read_text(encoding=encoding or self.default_encoding)
        self.logger.info(f"Reading tree structure from: {file_path}")
        return self.create_from_text(text, base_dir, dry_run)

    def _parse_tree(self, tree_text: str) -> List[TreeEntry]:
        lines = [ln.rstrip() for ln in tree_text.splitlines() if ln.strip()]
        if not lines:
            raise TreeParseError("Empty tree text")

        entries: List[TreeEntry] = []
        for idx, ln in enumerate(lines):
            ent = self._parse_line(ln, idx)
            if ent:
                entries.append(ent)
        return entries

    def _parse_line(self, line: str, line_idx: int) -> Optional[TreeEntry]:
        pattern = (
            r'^((?:[ ' + self.TREE_CHARS['vertical'] + ']*)*)'
            r'(?:' + re.escape(self.TREE_CHARS['branch']) +
            r' |' + re.escape(self.TREE_CHARS['last']) + r' )?(.*)$'
        )
        m = re.match(pattern, line)
        if not m:
            return None

        indent, raw = m.groups()
        # Remove inline comments (anything after '#')
        name = raw.split('#', 1)[0].rstrip()
        if not name:
            return None

        # Determine depth
        if line_idx == 0 and name.endswith('/'):
            depth = 0
        else:
            depth = (len(indent) // 4) + 1

        # Determine entry type
        if name.endswith('/'):
            entry_type = EntryType.DIRECTORY
            name = name.rstrip('/')
        else:
            entry_type = EntryType.FILE

        return TreeEntry(name=name, entry_type=entry_type, depth=depth)

    def _create_structure(self, entries: List[TreeEntry], base_path: Path, dry_run: bool):
        stack: List[str] = []
        for e in entries:
            stack = stack[:e.depth]
            parent = base_path.joinpath(*stack)
            full = parent / e.name
            e.path = full
            if e.entry_type is EntryType.DIRECTORY:
                self._make_dir(full, dry_run)
                stack.append(e.name)
            else:
                self._make_file(full, parent, dry_run)

    def _make_dir(self, path: Path, dry_run: bool):
        if dry_run:
            self.logger.debug(f"Would create directory: {path}")
        else:
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as ex:
                raise TreeCreationError(f"Failed to create directory '{path}': {ex}")
        self._stats['dirs_created'] += 1

    def _make_file(self, file_path: Path, parent: Path, dry_run: bool):
        if dry_run:
            self.logger.debug(f"Would create file: {file_path}")
        else:
            try:
                parent.mkdir(parents=True, exist_ok=True)
                file_path.touch(exist_ok=True)
            except Exception as ex:
                raise TreeCreationError(f"Failed to create file '{file_path}': {ex}")
        self._stats['files_created'] += 1

    def _reset_stats(self):
        self._stats = {'dirs_created': 0, 'files_created': 0}


def create_from_text(tree_text: str,
                     base_dir: Union[str, Path] = '.',
                     dry_run: bool = False,
                     logger: Optional[logging.Logger] = None) -> Dict[str, int]:
    return TreeCreator(logger).create_from_text(tree_text, base_dir, dry_run)


def create_from_file(file_path: Union[str, Path],
                     base_dir: Union[str, Path] = '.',
                     encoding: str = 'utf-8',
                     dry_run: bool = False,
                     logger: Optional[logging.Logger] = None) -> Dict[str, int]:
    return TreeCreator(logger).create_from_file(file_path, base_dir, encoding, dry_run)


def main():
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
""")
    parser.add_argument('input', nargs='?', help='Input tree file path (use "-" for stdin)')
    parser.add_argument('-b', '--base-dir', default='.', help='Base directory for structure creation')
    parser.add_argument('-e', '--encoding', default='utf-8', help='Input file encoding')
    parser.add_argument('-d', '--dry-run', action='store_true', help='Simulate creation without file operations')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('-V', '--version', action='version', version=f"tree-creator {__version__}")
    parser.add_argument('-I', '--issues', action='store_true', help="Open the project's GitHub issues page")

    args = parser.parse_args()
    if args.issues:
        webbrowser.open("https://github.com/jack-low/tree-creator/issues")
        return 0

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format='%(levelname)s: %(message)s')
    try:
        creator = TreeCreator()
        if args.input == '-':
            import sys
            stats = creator.create_from_text(sys.stdin.read(), args.base_dir, args.dry_run)
        else:
            stats = creator.create_from_file(args.input, args.base_dir, args.encoding, args.dry_run)

        print(f"\\nSummary: {stats['dirs_created']} directories, "
              f"{stats['files_created']} files "
              f"{'would be ' if args.dry_run else ''}created.")
    except Exception as ex:
        logging.error(f"Error: {ex}")
        return 1
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
