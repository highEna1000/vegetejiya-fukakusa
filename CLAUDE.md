# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

これは従業員のスキルと能力を追跡できるFlaskベースのスキル管理システム（スキルチェッカー）です。アプリケーションは2つのユーザー権限をサポートしています：スタッフと管理者。本番環境はRender.comでホスティングされています。

## 開発コマンド

### ローカル開発
```bash
# アプリケーション起動（デバッグモード）
python app.py

# 依存関係インストール
pip install -r requirements.txt
```

### デプロイメント
```bash
# 変更をコミットしてプッシュ（Renderで自動デプロイ）
git add .
git commit -m "変更内容の説明"
git push

# 本番環境URL: https://vegetejiya-fukakusa.onrender.com
```

## アーキテクチャ

### データベース設計
- **User**: 認証、権限（staff/admin）、初回ログイン状態、表示順序（order_index）を管理
- **Task**: スキル/タスクの定義（一意制約あり）、表示順序（order_index）を管理
- **UserSkill**: User-Task間のブール型能力マッピング（多対多関係）
- **Settings**: アプリケーション設定をkey-value形式で管理（スキル表示制限など）

**デュアルデータベース構成**：
- **開発環境**: SQLite（`database.db`）
- **本番環境**: PostgreSQL（`DATABASE_URL`環境変数で自動切り替え）

データベースは初回実行時に自動作成され、デフォルトの管理者アカウント（admin/password）が生成されます。

### 権限制御アーキテクチャ
- `@admin_required`デコレータによる管理者機能の制限
- Flask-Loginによるセッション管理
- ロールベースアクセス制御（管理者はユーザー・タスク管理、スタッフは閲覧のみ）

### UI/UXアーキテクチャ
- レスポンシブデザイン：768px以下でモバイル表示に自動切り替え
- デスクトップ：テーブル形式でのデータ表示
- モバイル：カード形式での直感的な操作
- スキル編集：モバイルではトグルスイッチ、デスクトップではチェックボックス

### 主要ルート
```
/ - ログインページ
/dashboard - スキルマトリックス表示（メイン画面）
/initial_setup - 新規ユーザーの初回スキル登録
/my_skills - 自分のスキル編集（全ユーザー）

# 管理者専用ルート
/admin/users - ユーザー管理（追加・編集・削除・順序変更）
/admin/tasks - タスク管理（追加・編集・削除・順序変更）
/admin/edit_skills/<user_id> - 個別ユーザーのスキル編集
/admin/edit_user/<user_id> - ユーザー情報編集
/admin/skill_stats - スキル統計表示
/admin/settings - アプリケーション設定（スキル表示制限など）
```

## 開発上の重要な注意点

### 言語とインターフェース
- すべてのUI、コメント、メッセージは日本語で統一
- フラッシュメッセージも日本語で表示

### データ整合性
- 新しいタスク追加時、既存全ユーザーに自動的にcan_do=Falseでスキルエントリを作成
- ユーザー削除時、関連するUserSkillレコードはカスケード削除
- 最後の管理者を削除・降格することは不可

### スタイリング
- `base.html`に統合されたレスポンシブCSS
- モバイルファーストのデザインアプローチ
- タッチ対応（ボタンは最小44px、入力欄は16px以上のフォントサイズ）
- カスタムトグルスイッチを使用したスキル設定UI

### セキュリティ
- WTFormsによるCSRF保護
- Werkzeugによるパスワードハッシュ化
- 環境変数による本番用SECRET_KEY設定
- 本番環境ではDEBUG=Falseに設定

## 環境変数とデプロイメント設定

### 環境変数
```bash
SECRET_KEY=your_secret_key_here          # 本番用秘密鍵
DATABASE_URL=postgresql://...            # PostgreSQL接続文字列（本番用）
DEBUG=False                              # デバッグモード制御
SKIP_DB_INIT=False                       # データベース初期化制御
CREATE_SAMPLE_DATA=True                  # サンプルデータ作成制御
PORT=5000                                # ポート番号
```

### データベース初期化とマイグレーション
```bash
# 開発環境でのデータベース初期化
python app.py  # 自動でinit_database()が実行される

# スキーママイグレーション（新しい列の追加など）
python migrate_db.py

# 開発用サンプルデータの作成
python seed_data.py          # サンプルデータ追加
python seed_data.py --reset  # データベースリセット後にサンプルデータ作成
```

### 本番デプロイメント
- **build.sh**: 自動ビルドスクリプト（依存関係インストール→マイグレーション実行）
- **Gunicorn**: 本番用WSGIサーバー
- **PostgreSQL**: 本番データベース（永続化）
- **Render.com**: 自動デプロイ（git pushで自動実行）

## 機能アーキテクチャ

### スキル表示制限システム
- **設定管理**: `Settings`モデルによる動的設定
- **制限モード**: スタッフは自分のスキルのみ表示
- **開放モード**: 全スタッフが互いのスキルを閲覧可能
- **管理者制御**: `/admin/settings`で動的切り替え可能

### 統計・分析機能
- **スキル統計**: 各スキルの習得率をプログレスバーで表示
- **管理者専用**: 'admin'ユーザーは統計計算から除外
- **リアルタイム**: データベース変更時に自動更新

### 順序管理システム
- **ユーザー順序**: `order_index`による表示順制御
- **タスク順序**: 同様の`order_index`システム
- **管理者操作**: 上下移動ボタンによる順序変更