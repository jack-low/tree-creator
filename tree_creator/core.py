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

import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Union, Tuple
import logging
from dataclasses import dataclass
from enum import Enum
from ._version import __version__

class EntryType(Enum):
    """Type of file system entry."""
    FILE = "file"
    DIRECTORY = "directory"


@dataclass
class TreeEntry:
    """Represents a single entry in the tree structure."""
    name: str
    entry_type: EntryType
    depth: int
    path: Optional[Path] = None


class TreeParseError(Exception):
    """Raised when tree parsing fails."""
    pass


class TreeCreationError(Exception):
    """Raised when file/directory creation fails."""
    pass


class TreeCreator:
    """
    Creates directory and file structures from tree-like text representations.
    
    Attributes:
        logger: Logger instance for debugging and error reporting
        default_encoding: Default encoding for file operations
    """
    
    # Tree drawing characters
    TREE_CHARS = {
        'vertical': '│',
        'branch': '├──',
        'last': '└──',
        'space': ' '
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None, 
                 default_encoding: str = 'utf-8'):
        """
        Initialize TreeCreator.
        
        Args:
            logger: Optional logger instance. If None, creates a default logger.
            default_encoding: Default encoding for file operations.
        """
        self.logger = logger or self._create_default_logger()
        self.default_encoding = default_encoding
        self._stats = {'dirs_created': 0, 'files_created': 0}
    
    def _create_default_logger(self) -> logging.Logger:
        """Create a default logger with console handler."""
        logger = logging.getLogger('TreeCreator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def create_from_text(self, tree_text: str, base_dir: Union[str, Path] = '.', 
                        dry_run: bool = False) -> Dict[str, int]:
        """
        Create directory and file structure from tree text.
        
        Args:
            tree_text: Tree-like text representation of the structure
            base_dir: Base directory where the structure will be created
            dry_run: If True, only simulate creation without actual file operations
            
        Returns:
            Dictionary with statistics about created directories and files
            
        Raises:
            TreeParseError: If the tree text cannot be parsed
            TreeCreationError: If file/directory creation fails
        """
        self._reset_stats()
        base_path = Path(base_dir).resolve()
        
        try:
            entries = self._parse_tree(tree_text)
            self._create_structure(entries, base_path, dry_run)
            
            if not dry_run:
                self.logger.info(f"Created structure in '{base_path}': "
                               f"{self._stats['dirs_created']} directories, "
                               f"{self._stats['files_created']} files")
            else:
                self.logger.info(f"Dry run completed. Would create: "
                               f"{self._stats['dirs_created']} directories, "
                               f"{self._stats['files_created']} files")
            
            return self._stats.copy()
            
        except Exception as e:
            self.logger.error(f"Failed to create structure: {e}")
            raise
    
    def create_from_file(self, file_path: Union[str, Path], base_dir: Union[str, Path] = '.', 
                        encoding: Optional[str] = None, dry_run: bool = False) -> Dict[str, int]:
        """
        Create directory and file structure from a tree file.
        
        Args:
            file_path: Path to file containing tree text
            base_dir: Base directory where the structure will be created
            encoding: File encoding (uses default if None)
            dry_run: If True, only simulate creation without actual file operations
            
        Returns:
            Dictionary with statistics about created directories and files
            
        Raises:
            FileNotFoundError: If the input file doesn't exist
            TreeParseError: If the tree text cannot be parsed
            TreeCreationError: If file/directory creation fails
        """
        file_path = Path(file_path)
        encoding = encoding or self.default_encoding
        
        if not file_path.exists():
            raise FileNotFoundError(f"Tree file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                tree_text = f.read()
            
            self.logger.info(f"Reading tree structure from: {file_path}")
            return self.create_from_text(tree_text, base_dir, dry_run)
            
        except Exception as e:
            self.logger.error(f"Failed to read tree file: {e}")
            raise
    
    def _parse_tree(self, tree_text: str) -> List[TreeEntry]:
        """
        Parse tree text into a list of TreeEntry objects.
        
        Args:
            tree_text: Tree-like text representation
            
        Returns:
            List of TreeEntry objects
            
        Raises:
            TreeParseError: If parsing fails
        """
        entries = []
        lines = [line.rstrip() for line in tree_text.splitlines() if line.strip()]
        
        if not lines:
            raise TreeParseError("Empty tree text")
        
        for idx, line in enumerate(lines):
            try:
                entry = self._parse_line(line, idx)
                if entry:
                    entries.append(entry)
            except Exception as e:
                raise TreeParseError(f"Failed to parse line {idx + 1}: '{line}' - {e}")
        
        return entries
    
    def _parse_line(self, line: str, line_idx: int) -> Optional[TreeEntry]:
        """
        Parse a single line into a TreeEntry.
        
        Args:
            line: Single line from tree text
            line_idx: Line index (0-based)
            
        Returns:
            TreeEntry object or None if line should be skipped
        """
        # Pattern to match tree structure
        pattern = r'^((?:[ ' + self.TREE_CHARS['vertical'] + ']*)*)(?:' + \
                 re.escape(self.TREE_CHARS['branch']) + ' |' + \
                 re.escape(self.TREE_CHARS['last']) + ' )?(.*)$'
        
        match = re.match(pattern, line)
        if not match:
            return None
        
        indent_str, name = match.groups()
        
        if not name:
            return None
        
        # Calculate depth
        if line_idx == 0 and name.endswith('/'):
            depth = 0
        else:
            # Count indent levels (4 spaces = 1 level)
            indent_levels = len(indent_str) // 4
            depth = indent_levels + 1
        
        # Determine entry type
        if name.endswith('/'):
            entry_type = EntryType.DIRECTORY
            name = name.rstrip('/')
        else:
            entry_type = EntryType.FILE
        
        return TreeEntry(name=name, entry_type=entry_type, depth=depth)
    
    def _create_structure(self, entries: List[TreeEntry], base_path: Path, 
                         dry_run: bool = False) -> None:
        """
        Create the actual directory and file structure.
        
        Args:
            entries: List of TreeEntry objects
            base_path: Base path for structure creation
            dry_run: If True, only simulate creation
        """
        stack = []  # Track directory path at each depth
        
        for entry in entries:
            # Adjust stack to current depth
            stack = stack[:entry.depth]
            
            # Build full path
            parent_path = base_path / Path(*stack)
            entry_path = parent_path / entry.name
            entry.path = entry_path
            
            if entry.entry_type == EntryType.DIRECTORY:
                self._create_directory(entry_path, dry_run)
                stack.append(entry.name)
            else:
                self._create_file(entry_path, parent_path, dry_run)
    
    def _create_directory(self, path: Path, dry_run: bool = False) -> None:
        """Create a directory."""
        if dry_run:
            self.logger.debug(f"Would create directory: {path}")
        else:
            try:
                path.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Created directory: {path}")
            except Exception as e:
                raise TreeCreationError(f"Failed to create directory '{path}': {e}")
        
        self._stats['dirs_created'] += 1
    
    def _create_file(self, file_path: Path, parent_path: Path, 
                    dry_run: bool = False) -> None:
        """Create a file."""
        if dry_run:
            self.logger.debug(f"Would create file: {file_path}")
        else:
            try:
                # Ensure parent directory exists
                parent_path.mkdir(parents=True, exist_ok=True)
                
                # Create empty file
                file_path.touch()
                self.logger.debug(f"Created file: {file_path}")
            except Exception as e:
                raise TreeCreationError(f"Failed to create file '{file_path}': {e}")
        
        self._stats['files_created'] += 1
    
    def _reset_stats(self) -> None:
        """Reset creation statistics."""
        self._stats = {'dirs_created': 0, 'files_created': 0}


# Convenience functions
def create_from_text(tree_text: str, base_dir: Union[str, Path] = '.', 
                    dry_run: bool = False, logger: Optional[logging.Logger] = None) -> Dict[str, int]:
    """
    Convenience function to create structure from text.
    
    See TreeCreator.create_from_text for details.
    """
    creator = TreeCreator(logger=logger)
    return creator.create_from_text(tree_text, base_dir, dry_run)


def create_from_file(file_path: Union[str, Path], base_dir: Union[str, Path] = '.', 
                    encoding: str = 'utf-8', dry_run: bool = False, 
                    logger: Optional[logging.Logger] = None) -> Dict[str, int]:
    """
    Convenience function to create structure from file.
    
    See TreeCreator.create_from_file for details.
    """
    creator = TreeCreator(logger=logger)
    return creator.create_from_file(file_path, base_dir, encoding, dry_run)


# CLI interface
def main():
    """Command-line interface for tree creator."""
    import argparse
    
    parser = argparse.ArgumentParser(
        prog="tree-creator",
        description='Create directory and file structures from tree-like text representations.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Example tree file (tree.txt):
    project/
    ├── src/
    │   ├── main.py
    │   └── utils.py
    └── README.md

Usage:
    python tree_creator.py tree.txt --base-dir ./my_project
    python tree_creator.py tree.txt --dry-run
    echo "dir/\\n└── file.txt" | python tree_creator.py -
        '''
    )
    
    parser.add_argument('input', nargs='?', help='Input tree file path (use "-" for stdin)')
    parser.add_argument('-b', '--base-dir', default='.', help='Base directory for structure creation (default: current directory)')
    parser.add_argument('-e', '--encoding', default='utf-8', help='Input file encoding (default: utf-8)')
    parser.add_argument('-d', '--dry-run', action='store_true', help='Simulate creation without actual file operations')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    
    parser.add_argument("-V", "--version", action="version", version=f"tree-creator {__version__}")
    parser.add_argument("-I", "--issues", action="store_true", help="Open the project's GitHub issues page in your browser")

    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
    
    # Handle --issues
    if args.issues:
        import webbrowser
        webbrowser.open("https://github.com/jack-low/tree-creator/issues")
        return 0
        
    try:
        creator = TreeCreator()
        
        if args.input == '-':
            # Read from stdin
            import sys
            tree_text = sys.stdin.read()
            stats = creator.create_from_text(tree_text, args.base_dir, args.dry_run)
        else:
            # Read from file
            stats = creator.create_from_file(args.input, args.base_dir, 
                                           args.encoding, args.dry_run)
        
        print(f"\nSummary: {stats['dirs_created']} directories, "
              f"{stats['files_created']} files {'would be ' if args.dry_run else ''}created.")
        
    except Exception as e:
        logging.error(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())