# 📁 Tree Creator（ツリークリエイター）

![PyPI](https://img.shields.io/pypi/v/tree-creator)
![Python Versions](https://img.shields.io/pypi/pyversions/tree-creator)
![License](https://img.shields.io/pypi/l/tree-creator)

🌐 言語:  [English version](./README.md) | [日本語はこちら](./README.ja.md)

`tree` コマンドのようなテキスト表現から、ディレクトリやファイルの構造を自動生成するツールです。

## ✨ 特長

- ツリー形式のテキストから、対応するディレクトリ／ファイルを作成
- ドライラン（dry-run）対応：実際に作成せずに構造を確認
- Python API & コマンドライン対応
- ログ出力によるデバッグ／記録に対応
- 依存ライブラリなし（標準ライブラリのみ）

## 📦 インストール

```bash
pip install tree-creator
```

または、開発環境でのインストール：

```bash
git clone https://github.com/jack-low/tree-creator
cd tree-creator
pip install -e ".[dev]"
```

## 🚀 使い方

### ✨ Python API からの使用例

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

### 💻 コマンドラインからの使用
### 🧪 EOF（Here Document）での使用例

以下のように、複数行のツリー構造を標準入力で直接渡すことができます：

```bash
tree-creator -b ./output-dir -d - <<EOF
myapp/
├── index.html
└── static/
    └── style.css
EOF
```

- `-d` はドライラン（実際には作成されません）
- `-b ./output-dir` で出力先ディレクトリを指定
- `-` は標準入力から読み込む指定です


```bash
tree-creator tree.txt --base-dir ./my_project
tree-creator tree.txt --dry-run
echo "dir/\n└── file.txt" | tree-creator -
```

#### オプション一覧

| オプション       | 説明                                      |
|------------------|-------------------------------------------|
| `-b, --base-dir` | 作成先のベースディレクトリ（デフォルト: `.`） |
| `-e, --encoding` | 入力ファイルのエンコーディング（デフォルト: `utf-8`） |
| `-d, --dry-run`  | 実際には作成せず、シミュレーションのみ実行 |
| `-v, --verbose`  | 詳細なログを出力                          |

## 📄 ツリーフォーマットの例

以下のように、`tree` コマンドの出力形式に準じた書き方を使用します：

```
project/
├── src/
│   ├── main.py
│   └── utils.py
└── README.md
```

- ディレクトリは末尾に `/` を付けます
- 使用文字：`├──`、`└──`、`│` など

## 🧪 開発用コマンド

テスト実行：

```bash
pytest
```

コード整形とチェック：

```bash
black .
flake8 .
mypy tree_creator
```

## 📜 ライセンス

MITライセンス © [Jack3Low](mailto:xapa.pw@gmail.com)

## 🔗 関連リンク

* [PyPI tree-creator](https://pypi.org/project/tree-creator/)
- [ソースコード](https://github.com/jack-low/tree-creator)
- [Issue トラッカー](https://github.com/jack-low/tree-creator/issues)
- [ドキュメント](https://github.com/jack-low/tree-creator#readme)
 - [変更履歴 (Changelog)](./CHANGELOG.md)
