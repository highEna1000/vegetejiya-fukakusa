#!/usr/bin/env python3
"""
エクスポートしたデータをSupabaseにインポートするスクリプト
"""
import os
import json
from app import app, db, User, Task, UserSkill, Settings

def migrate_to_supabase():
    """JSONファイルからデータをSupabaseにインポート"""
    if not os.path.exists('database_export.json'):
        print("❌ database_export.json が見つかりません。")
        print("先にexport_data.pyを実行してください。")
        return False
    
    with app.app_context():
        try:
            # JSONファイルを読み込み
            with open('database_export.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print("📊 インポート予定データ:")
            print(f"- ユーザー: {len(data['users'])}件")
            print(f"- タスク: {len(data['tasks'])}件")
            print(f"- スキル: {len(data['user_skills'])}件")
            print(f"- 設定: {len(data['settings'])}件")
            
            # 現在のSupabaseデータを確認
            current_users = User.query.count()
            current_tasks = Task.query.count()
            current_skills = UserSkill.query.count()
            current_settings = Settings.query.count()
            
            print(f"\n📊 現在のSupabaseデータ:")
            print(f"- ユーザー: {current_users}件")
            print(f"- タスク: {current_tasks}件")
            print(f"- スキル: {current_skills}件")
            print(f"- 設定: {current_settings}件")
            
            # タスクデータをインポート（重複チェック）
            print("\n🔄 タスクデータをインポートしています...")
            imported_tasks = 0
            for task_data in data['tasks']:
                existing_task = Task.query.filter_by(name=task_data['name']).first()
                if not existing_task:
                    task = Task(
                        name=task_data['name'],
                        order_index=task_data['order_index']
                    )
                    db.session.add(task)
                    imported_tasks += 1
            
            db.session.commit()
            print(f"✅ タスク {imported_tasks}件をインポートしました")
            
            # ユーザーデータをインポート（adminは除く、重複チェック）
            print("\n🔄 ユーザーデータをインポートしています...")
            imported_users = 0
            for user_data in data['users']:
                if user_data['username'] == 'admin':
                    continue  # 管理者は既に存在するのでスキップ
                
                existing_user = User.query.filter_by(username=user_data['username']).first()
                if not existing_user:
                    user = User(
                        username=user_data['username'],
                        password_hash=user_data['password_hash'],
                        role=user_data['role'],
                        is_first_login=user_data['is_first_login'],
                        order_index=user_data['order_index']
                    )
                    db.session.add(user)
                    imported_users += 1
            
            db.session.commit()
            print(f"✅ ユーザー {imported_users}件をインポートしました")
            
            # ユーザースキルデータをインポート
            print("\n🔄 スキルデータをインポートしています...")
            imported_skills = 0
            for skill_data in data['user_skills']:
                # ユーザーとタスクの存在確認
                user = User.query.get(skill_data['user_id'])
                task = Task.query.get(skill_data['task_id'])
                
                if user and task:
                    # 重複チェック
                    existing_skill = UserSkill.query.filter_by(
                        user_id=skill_data['user_id'],
                        task_id=skill_data['task_id']
                    ).first()
                    
                    if not existing_skill:
                        skill = UserSkill(
                            user_id=skill_data['user_id'],
                            task_id=skill_data['task_id'],
                            can_do=skill_data['can_do']
                        )
                        db.session.add(skill)
                        imported_skills += 1
            
            db.session.commit()
            print(f"✅ スキル {imported_skills}件をインポートしました")
            
            # 設定データの更新（skill_visibilityのみ）
            print("\n🔄 設定データを確認しています...")
            for setting_data in data['settings']:
                if setting_data['key'] == 'skill_visibility':
                    existing_setting = Settings.query.filter_by(key='skill_visibility').first()
                    if existing_setting and existing_setting.value != setting_data['value']:
                        existing_setting.value = setting_data['value']
                        print(f"✅ 設定 'skill_visibility' を '{setting_data['value']}' に更新しました")
            
            db.session.commit()
            
            # 最終確認
            final_users = User.query.count()
            final_tasks = Task.query.count()
            final_skills = UserSkill.query.count()
            final_settings = Settings.query.count()
            
            print(f"\n🎉 データ移行完了！")
            print(f"📊 移行後のSupabaseデータ:")
            print(f"- ユーザー: {final_users}件")
            print(f"- タスク: {final_tasks}件")
            print(f"- スキル: {final_skills}件")
            print(f"- 設定: {final_settings}件")
            
            return True
            
        except Exception as e:
            print(f"❌ データ移行エラー: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    migrate_to_supabase()