# マニュアルサポートアプリケーション

## 概要
PDFマニュアルをアップロードして、AI による要約音声生成と質疑応答機能を提供するWebアプリケーション。

## 主な機能
- PDFマニュアルのアップロード
- RAG（Retrieval-Augmented Generation）による詳細な要約生成（15000文字対応）
- OpenAI TTS による音声読み上げ
- マニュアル内容に基づく質疑応答（参照ページ情報付き）
- シンプルなモノトーンUI

## 技術スタック
- **Backend**: Flask
- **PDF処理**: pypdf
- **AI/ML**: OpenAI API（GPT-3.5-turbo, TTS-1）
- **RAG**: LangChain + ChromaDB
- **Frontend**: Bootstrap 5 + JavaScript
- **パッケージ管理**: UV

## セットアップ

### 1. 環境構築
```bash
cd manual_support
uv init .
uv add flask pypdf openai python-dotenv langchain langchain-openai langchain-community chromadb tiktoken cryptography
```

### 2. 環境変数設定
`.env`ファイルを作成:
```
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_here
```

### 3. アプリケーション起動
```bash
uv run python main.py
```

## デプロイ方法

### Railway デプロイ（推奨・無料枠あり）

1. [Railway](https://railway.app) にサインアップ
2. GitHubリポジトリと連携
3. 環境変数を Railway ダッシュボードで設定:
   - `OPENAI_API_KEY`
   - `SECRET_KEY`
4. 自動デプロイが開始

### Render デプロイ（無料枠あり）

1. [Render](https://render.com) にサインアップ
2. "New Web Service" を作成
3. GitHubリポジトリを選択
4. 設定:
   - Build Command: `uv sync`
   - Start Command: `uv run python main.py`
5. 環境変数を設定

### Vercel デプロイ（無料枠あり）

1. [Vercel](https://vercel.com) にサインアップ
2. GitHubリポジトリをインポート
3. `vercel.json` を作成:
```json
{
  "builds": [
    {
      "src": "main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "main.py"
    }
  ]
}
```

### Heroku デプロイ（有料）

#### 1. 必要ファイルの準備
```bash
# requirements.txt作成
uv export --format requirements-txt > requirements.txt

# runtime.txt作成
echo "python-3.12.3" > runtime.txt

# Procfile作成
echo "web: python main.py" > Procfile
```

#### 2. main.py の修正
```python
# 最後の部分を以下に変更
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
```

#### 3. Heroku CLI でデプロイ
```bash
# Heroku CLI インストール
# https://devcenter.heroku.com/articles/heroku-cli

# ログイン
heroku login

# アプリ作成
heroku create your-app-name

# 環境変数設定
heroku config:set OPENAI_API_KEY=your_api_key_here
heroku config:set SECRET_KEY=your_secret_key_here

# Git設定とデプロイ
git init
git add .
git commit -m "Initial commit"
git push heroku main
```


## プロダクション環境での注意事項

### 1. ファイルストレージ
現在はローカルファイルシステムを使用しているため、クラウドストレージ（AWS S3等）への移行を推奨:

```python
# AWS S3 例
import boto3
s3_client = boto3.client('s3')
```

### 2. データベース永続化
ChromaDBの永続化ディレクトリもクラウドストレージに移行:

```python
# クラウドストレージ対応例
VECTOR_DB_FOLDER = 's3://your-bucket/vector_db'
```

### 3. セキュリティ
- API キーの適切な管理
- HTTPS の使用
- ファイルアップロードサイズ制限の設定

### 4. パフォーマンス最適化
- Redis等のキャッシュシステム導入
- CDN の使用
- 並列処理の実装

## アーキテクチャ

### RAG システム
1. PDFテキスト抽出（pypdf）
2. テキストチャンク分割（1000文字、200文字オーバーラップ）
3. ベクトル埋め込み生成（OpenAI Embeddings）
4. ベクトルストア（ChromaDB）
5. 類似度検索（質問に関連するチャンク抽出）
6. LLM生成（関連チャンクのみを使用）

### ディレクトリ構造
```
manual_support/
├── main.py                 # メインアプリケーション
├── templates/
│   ├── index.html         # アップロードページ
│   └── manual_detail.html # 要約・質疑応答ページ
├── static/css/
│   └── style.css          # スタイルシート
├── uploads/               # アップロードファイル
├── audio/                 # 生成音声ファイル
├── vector_db/             # ベクトルデータベース
├── .env                   # 環境変数
└── CLAUDE.md             # このファイル
```

## API エンドポイント

- `GET /` - アップロードページ
- `POST /upload` - ファイルアップロード
- `GET /manual/<filename>` - 要約・質疑応答ページ
- `GET /api/generate_summary/<filename>` - 要約生成
- `POST /api/chat` - 質疑応答
- `GET /audio/<filename>` - 音声ファイル配信

## 開発メモ

### 実装済み機能
- ✅ PDFアップロード・解析
- ✅ RAGベース要約生成（15000文字）
- ✅ OpenAI TTS音声生成
- ✅ RAGベース質疑応答（参照ページ付き）
- ✅ レスポンシブUI（モノトーンデザイン）
- ✅ フッター注意喚起

### 今後の改善案
- クラウドストレージ対応
- ユーザー認証システム
- マニュアル管理機能
- 複数言語対応
- 音声品質向上（voice選択）

## トラブルシューティング

### よくある問題
1. **OpenAI API エラー**: API キーの確認
2. **PDF読み込みエラー**: cryptography ライブラリの確認
3. **音声生成失敗**: ネットワーク接続の確認
4. **メモリ不足**: 大きなPDFの場合はチャンクサイズ調整

### ログ確認
```bash
# アプリケーションログ
tail -f logs/app.log

# Heroku ログ
heroku logs --tail
```

## ライセンス
このプロジェクトはMITライセンスの下で公開されています。