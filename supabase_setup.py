#!/usr/bin/env python3
"""
Supabaseでテーブル作成とデータ移行を行うスクリプト
Render環境で実行される想定
"""
import os
from app import app, db, User, Task, UserSkill, Settings

def setup_supabase():
    """Supabaseでテーブル作成"""
    with app.app_context():
        try:
            print("🔄 Supabaseでテーブル作成中...")
            
            # テーブル作成
            db.create_all()
            
            print("✅ テーブル作成完了")
            
            # 基本データの確認
            user_count = User.query.count()
            task_count = Task.query.count()
            skill_count = UserSkill.query.count()
            setting_count = Settings.query.count()
            
            print(f"📊 現在のデータ:")
            print(f"- ユーザー: {user_count}件")
            print(f"- タスク: {task_count}件")
            print(f"- スキル: {skill_count}件")
            print(f"- 設定: {setting_count}件")
            
            return True
            
        except Exception as e:
            print(f"❌ エラー: {e}")
            return False

if __name__ == "__main__":
    setup_supabase()