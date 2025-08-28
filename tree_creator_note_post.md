## Tree Creator パッケージ紹介

`Tree Creator` は、テキスト形式のツリー構造をもとに、対応するディレクトリとファイルを自動生成する Python パッケージです。
ブログプラットフォーム「note」でのシェアを想定し、インストール方法から詳しいコード解説までまとめました。

---

### 🔍 目次
1. 概要
2. 特長
3. インストール
4. 使い方
5. コード解説
   - バージョン管理
   - 行末コメント対応パース
   - 構造生成ロジック
   - CLI 実装
6. サンプル
7. おわりに

---

### 1. 概要
`Tree Creator` は、Unix の `tree` コマンドのように、
以下のようなテキストツリーを入力すると…
```text
project/
├── src/
│   ├── main.py
│   └── utils.py
└── README.md
```
自動で `project` フォルダ以下に同じ構造を作成します。
パスワード、ネットワーク設定不要で、標準ライブラリのみで動作します。

---

### 2. 特長
- テキストベースでディレクトリ／ファイルを自動生成
- `dry-run` モードでシミュレーション可能
- 行末コメント (`# 説明文`) を無視して正確にパース
- バージョン情報を一元管理 (`_version.py`)
- CLI では `--version`, `--issues`, `--help` をサポート

---

### 3. インストール
```bash
pip install tree-creator
```
開発モード（ソースを直接反映）:
```bash
git clone https://github.com/jack-low/tree-creator.git
cd tree-creator
pip install -e .
```

---

### 4. 使い方
#### Python API
```python
from tree_creator import TreeCreator

text = '''
myapp/
├── index.html      # Index File
└── static/
    └── style.css   # style sheet
'''

creator = TreeCreator()
stats = creator.create_from_text(text, base_dir='./output', dry_run=False)
print(stats)  # {'dirs_created': 2, 'files_created': 2}
```

#### CLI
```bash
# 標準的な使い方
tree-creator tree.txt --base-dir ./output

# dry-run
tree-creator tree.txt --dry-run

# 標準入力と Here Document
tree-creator -b ./output -d - <<EOF
myapp/
├── index.html      # Index File
└── static/
    └── style.css   # style sheet
EOF

# バージョン確認
tree-creator --version

# バグ報告ページを開く
tree-creator --issues
```

---

### 5. コード解説
以下、主要な部分をご紹介します。

#### 5.1 バージョン管理 (`_version.py`)
```python
# tree_creator/_version.py
__version__ = "1.1.3"
```
- この一箇所を更新するだけで、CLI と `setup.py` 両方に反映されます。

#### 5.2 行末コメント対応パース
```python
def _parse_line(self, line: str, idx: int) -> Optional[TreeEntry]:
    # マッチパターン
    m = re.match(pattern, line)
    if not m:
        return None
    indent, raw = m.groups()
    # 行末コメントを除去
    name = raw.split('#', 1)[0].rstrip()
    if not name:
        return None
    # ディレクトリ深度を算出
    depth = (len(indent)//4) + (0 if idx==0 and name.endswith('/') else 1)
    # ファイル or ディレクトリ種別判定
    if name.endswith('/'):
        entry_type = EntryType.DIRECTORY
        name = name.rstrip('/')
    else:
        entry_type = EntryType.FILE
    return TreeEntry(name, entry_type, depth)
```
- `#` 以降を切り捨てることで、コメント付きの行も正しく処理します。

#### 5.3 構造生成ロジック
```python
for entry in entries:
    # スタックを深さに合わせ調整
    stack = stack[:entry.depth]
    parent = base_path.joinpath(*stack)
    path = parent / entry.name
    if entry.entry_type is EntryType.DIRECTORY:
        path.mkdir(parents=True, exist_ok=True)
        stack.append(entry.name)
    else:
        parent.mkdir(parents=True, exist_ok=True)
        path.touch()
```
- 追加するパスをスタックで管理し、深さごとに適切な親ディレクトリを設定

#### 5.4 CLI 実装
```python
parser = argparse.ArgumentParser(...)
# オプション定義
parser.add_argument('-V','--version', action='version', version=f"tree-creator {__version__}")
parser.add_argument('-I','--issues', action='store_true', help="Open GitHub issues page")
args = parser.parse_args()
if args.issues:
    webbrowser.open("https://github.com/jack-low/tree-creator/issues")
    return 0
# 入力処理
```
- `--issues` で GitHub の Issues ページを開く機能を追加

---

### 6. サンプル
```bash
# プロジェクトルートで
tree-creator -b ./demo - <<EOF
site/
├── index.html
├── about.html
└── assets/
    └── main.css  # メインスタイル
EOF
```
実行結果:
```
Dry run completed. Would create: 3 directories, 3 files

Summary: 3 directories, 3 files would be created.
```

---

### 7. PyPI への公開

`Tree Creator` を PyPI に公開する方法をまとめます。

**ビルドと検証**
```bash
python -m build                # ソースと Wheel を dist/ に生成
twine check dist/*             # long_description 等の検証
```

**本番環境へのアップロード**
```bash
twine upload dist/*            # PyPI (https://pypi.org) にアップロード
```
- ユーザー名: `__token__`
- パスワード: GitHub Secrets 等で管理した `PYPI_TOKEN`

**TestPyPI での検証**
```bash
twine upload --repository testpypi dist/*
```

---

### 8. GitHub での管理

プロジェクトは GitHub で管理し、下記の仕組みを整えると効率的です。

- **リポジトリ作成**
```bash
gh repo create <ユーザー名>/tree-creator --public --source=. --push
```
- **CI/CD（GitHub Actions）**
  - `.github/workflows/publish-to-pypi.yml` を配置し、`PYPI_TOKEN` を Secrets に設定
  - プッシュやタグ付けで自動ビルド＆公開
- **シークレット管理**
  - GitHub Settings > Secrets and variables > Actions で以下を登録:
    - `PYPI_TOKEN` (PyPI API トークン)
    - `GITHUB_TOKEN` (必要に応じて)

---

### 9. おわりに

- **OSS への貢献歓迎！**
- バグ報告・機能提案は [Issues](https://github.com/jack-low/tree-creator/issues) へ。
- プルリクエストもお待ちしています。

ぜひご活用ください！🎉
`Tree Creator` を使えば、プロジェクト構造のひな形作成やテスト用ディレクトリの準備が瞬時に完了します。
ぜひ試してみてください！

---

✏️ **GitHub**: https://github.com/jack-low/tree-creator

✉️ **Issues**: https://github.com/jack-low/tree-creator/issues
