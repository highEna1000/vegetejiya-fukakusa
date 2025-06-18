# スキルチェッカー

従業員のスキルと能力を追跡できるFlaskベースのスキル管理システムです。

## 機能

- ユーザー管理（スタッフ・管理者）
- スキル/タスク管理
- スキルマトリックス表示
- モバイル対応UI
- ドラッグアンドドロップでの順序変更
- スキル検索機能（管理者のみ）

## セットアップ

### 開発環境

1. **依存関係のインストール**
```bash
pip install -r requirements.txt
```

2. **初回起動（サンプルデータ付き）**
```bash
python app.py
```

3. **サンプルデータのみ作成**
```bash
python seed_data.py
```

4. **データベースリセット**
```bash
python seed_data.py --reset
```

### 初期設定

#### 管理者ユーザー
初回起動時にデフォルトの管理者ユーザーが作成されます。
管理者ユーザーでログイン後、必ず以下を実行してください：

1. 管理者のパスワードを変更
2. 不要なサンプルユーザーを削除
3. 実際のスタッフユーザーを追加

## データ永続化

### 開発環境
- SQLiteデータベース（`database.db`）を使用
- データは永続化されます

### 本番環境（Render.com）
- PostgreSQLデータベースを使用
- 環境変数`DATABASE_URL`でPostgreSQL接続を設定

## 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `DATABASE_URL` | データベース接続URL | SQLiteを使用 |
| `SECRET_KEY` | Flaskのシークレットキー | `your_secret_key...` |
| `DEBUG` | デバッグモード | `false` |
| `SKIP_DB_INIT` | データベース初期化をスキップ | `false` |
| `CREATE_SAMPLE_DATA` | サンプルデータを作成 | 開発環境のみ`true` |
| `PORT` | サーバーポート | `5000` |

## 開発時のワークフロー

1. **コード変更後のテスト**
```bash
python app.py
```

2. **データをリセットしたい場合**
```bash
python seed_data.py --reset
```

3. **新しい機能追加後**
- ローカルで動作確認
- 必要に応じてサンプルデータを調整
- デプロイ

## デプロイ

### Render.com
1. PostgreSQLデータベースを作成
2. 環境変数`DATABASE_URL`にPostgreSQL URLを設定
3. Gitリポジトリと連携してデプロイ

## トラブルシューティング

### データが消える場合
- 開発環境: `database.db`ファイルが削除されていないか確認
- 本番環境: PostgreSQLが正しく設定されているか確認

### マイグレーションエラー
```bash
python migrate_db.py
```

### 初期化をやり直したい場合
```bash
python seed_data.py --reset
```