# 名刺スキャンアプリ

名刺画像をアップロードすると：
1. Claude Vision APIで名刺情報を自動抽出
2. Google Sheetsに行追加
3. GmailにAI生成の御礼メール下書きを作成

## セットアップ

### 1. 依存パッケージのインストール

```bash
cd examples/meishi-app
pip install -r requirements.txt
```

### 2. Google Cloud Console の設定

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成
2. 以下のAPIを有効化：
   - Google Sheets API
   - Gmail API
3. 「認証情報」→「OAuthクライアントID」→「デスクトップアプリ」で認証情報を作成
4. `credentials.json` としてダウンロードし、このディレクトリに配置

### 3. 環境変数の設定

```bash
cp .env.example .env
```

`.env` を編集して以下を入力：

| 変数名 | 内容 |
|--------|------|
| `ANTHROPIC_API_KEY` | Anthropic APIキー |
| `SPREADSHEET_ID` | Google SheetsのURL末尾のID |
| `SHEET_NAME` | シート名（デフォルト：名刺データ） |
| `SENDER_EMAIL` | 送信元メールアドレス |

### 4. Google認証（初回のみ）

```bash
python google_services.py
```

ブラウザが開くので、Googleアカウントでログインして認証します。`token.json` が生成されます。

### 5. 起動

```bash
uvicorn main:app --reload --port 8000
```

ブラウザで `http://localhost:8000` にアクセス。

## 使い方

1. 名刺の画像（JPEG/PNG/WebP、5MB以下）をアップロード
2. 御礼メールに入れたい内容を箇条書きで記入（任意）
3. 「名刺を処理する」ボタンをクリック

### 処理結果

- **名刺情報**：抽出された氏名・会社・役職・連絡先など
- **スプレッドシート**：自動的に1行追加される
- **Gmail下書き**：メモが入力された場合のみ作成される

## ファイル構成

```
meishi-app/
├── main.py              # FastAPIアプリ本体
├── google_services.py   # Google Sheets / Gmail 連携
├── templates/
│   └── index.html       # フロントエンドUI
├── requirements.txt
├── .env.example
└── README.md
```

## 注意事項

- `credentials.json` と `token.json` は `.gitignore` に追加してください
- Google OAuthの初回認証は「デスクトップアプリ」として設定してください
- メールアドレスが名刺に記載されていない場合は下書きを作成しません
