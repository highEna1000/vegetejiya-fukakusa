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
- **User**: 認証、権限（staff/admin）、初回ログイン状態、表示順序を管理
- **Task**: スキル/タスクの定義（一意制約あり）
- **UserSkill**: User-Task間のブール型能力マッピング（多対多関係）

SQLiteデータベース（`database.db`）は初回実行時に自動作成され、デフォルトの管理者アカウント（admin/password）が生成されます。

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
/admin/users - ユーザー管理（追加・編集・削除・順序変更）
/admin/tasks - タスク管理（追加・編集・削除）
/admin/edit_skills/<user_id> - 個別ユーザーのスキル編集
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