#!/usr/bin/env python3
"""
エクスポートしたデータをSupabaseにインポートするスクリプト
"""
import os
import json
from app import app, db, User, Task, UserSkill, Settings

def import_data():
    """JSONファイルからデータをインポート"""
    if not os.path.exists('database_export.json'):
        print("database_export.json が見つかりません。")
        return
    
    with app.app_context():
        # 既存データをクリア（注意：既存データは削除される）
        print("既存データをクリアしています...")
        UserSkill.query.delete()
        Settings.query.delete()
        Task.query.delete()
        User.query.delete()
        db.session.commit()
        
        # JSONファイルを読み込み
        with open('database_export.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # ユーザーデータをインポート
        print("ユーザーデータをインポートしています...")
        for user_data in data['users']:
            user = User(
                id=user_data['id'],
                username=user_data['username'],
                password_hash=user_data['password_hash'],
                role=user_data['role'],
                is_first_login=user_data['is_first_login'],
                order_index=user_data['order_index']
            )
            db.session.add(user)
        
        # タスクデータをインポート
        print("タスクデータをインポートしています...")
        for task_data in data['tasks']:
            task = Task(
                id=task_data['id'],
                name=task_data['name'],
                order_index=task_data['order_index']
            )
            db.session.add(task)
        
        # 設定データをインポート
        print("設定データをインポートしています...")
        for setting_data in data['settings']:
            setting = Settings(
                id=setting_data['id'],
                key=setting_data['key'],
                value=setting_data['value']
            )
            db.session.add(setting)
        
        # まず基本データをコミット
        db.session.commit()
        
        # ユーザースキルデータをインポート
        print("スキルデータをインポートしています...")
        for skill_data in data['user_skills']:
            skill = UserSkill(
                id=skill_data['id'],
                user_id=skill_data['user_id'],
                task_id=skill_data['task_id'],
                can_do=skill_data['can_do']
            )
            db.session.add(skill)
        
        db.session.commit()
        
        print(f"データインポート完了:")
        print(f"- ユーザー: {len(data['users'])}件")
        print(f"- タスク: {len(data['tasks'])}件")
        print(f"- スキル: {len(data['user_skills'])}件")
        print(f"- 設定: {len(data['settings'])}件")

if __name__ == "__main__":
    import_data()