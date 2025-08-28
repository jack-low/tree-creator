# 📁 Tree Creator

![PyPI](https://img.shields.io/pypi/v/tree-creator)
![Python Versions](https://img.shields.io/pypi/pyversions/tree-creator)
![License](https://img.shields.io/pypi/l/tree-creator)
[![CI](https://github.com/jack-low/tree-creator/actions/workflows/ci.yml/badge.svg)](https://github.com/jack-low/tree-creator/actions/workflows/ci.yml)
[![Publish](https://github.com/jack-low/tree-creator/actions/workflows/publish.yml/badge.svg)](https://github.com/jack-low/tree-creator/actions/workflows/publish.yml)

Create directory and file structures from tree-like text representations — just like the output of the `tree` command.

## ✨ Features

* Parse text-based tree structures and generate corresponding directories and files.
* Dry-run support (simulate without creating files).
* CLI and API support.
* Helpful logging for debugging and auditing.
* Version managed centrally via `_version.py`.
* Zero external dependencies.

## 📦 Installation

```bash
pip install tree-creator
```

or (for development):

```bash
git clone https://github.com/jack-low/tree-creator
cd tree-creator
pip install -e ".[dev]"
```

## 🚀 Usage

### ✨ Example (Python API)

```python
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
```

### 💻 CLI

```bash
tree-creator tree.txt --base-dir ./my_project
tree-creator tree.txt --dry-run
echo "dir/\n└── file.txt" | tree-creator -
```

### 🧪 Example using Here Document (EOF)

```bash
tree-creator -b ./output-dir -d - <<EOF
myapp/
├── index.html
└── static/
    └── style.css
EOF
```

- `-d` enables dry-run mode
- `-b ./output-dir` sets the output base directory
- `-` reads from stdin

#### Options

| Option           | Description                                |
|------------------|--------------------------------------------|
| `-b, --base-dir` | Target base directory (default: `.`)       |
| `-e, --encoding` | Encoding for input file (default: `utf-8`) |
| `-d, --dry-run`  | Simulate without file creation             |
| `-v, --verbose`  | Verbose log output                         |
| `-V, --version`  | Display version                            |

## 📄 Tree Format

A valid tree structure should follow conventions like:

```
project/
├── src/
│   ├── main.py
│   └── utils.py
└── README.md
```

- Directories end with `/`
- Use characters like `├──`, `└──`, `│`

## 🧪 Development

```bash
pip install -e ".[dev]"
pytest
black .
flake8 .
mypy tree_creator
```

## 📜 License

MIT License © [Jack3Low](mailto:xapa.pw@gmail.com)

## 🔗 Links

* [PyPI tree-creator](https://pypi.org/project/tree-creator/)
* [Source Code](https://github.com/jack-low/tree-creator)
* [Issue Tracker](https://github.com/jack-low/tree-creator/issues)
* [Documentation](https://github.com/jack-low/tree-creator#readme)
* [Japanese README](https://github.com/jack-low/tree-creator/blob/main/README.ja.md)
* [Changelog](./CHANGELOG.md)
