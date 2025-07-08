#!/usr/bin/env python3
"""
現在のデータベースからデータをエクスポートするスクリプト
"""
import os
import json
from app import app, db, User, Task, UserSkill, Settings

def export_data():
    """データベースからすべてのデータをJSON形式でエクスポート"""
    with app.app_context():
        # データを辞書形式で取得
        data = {
            'users': [],
            'tasks': [],
            'user_skills': [],
            'settings': []
        }
        
        # ユーザーデータ
        users = User.query.all()
        for user in users:
            data['users'].append({
                'id': user.id,
                'username': user.username,
                'password_hash': user.password_hash,
                'role': user.role,
                'is_first_login': user.is_first_login,
                'order_index': user.order_index
            })
        
        # タスクデータ
        tasks = Task.query.all()
        for task in tasks:
            data['tasks'].append({
                'id': task.id,
                'name': task.name,
                'order_index': task.order_index
            })
        
        # ユーザースキルデータ
        user_skills = UserSkill.query.all()
        for skill in user_skills:
            data['user_skills'].append({
                'id': skill.id,
                'user_id': skill.user_id,
                'task_id': skill.task_id,
                'can_do': skill.can_do
            })
        
        # 設定データ
        settings = Settings.query.all()
        for setting in settings:
            data['settings'].append({
                'id': setting.id,
                'key': setting.key,
                'value': setting.value
            })
        
        # JSONファイルに保存
        with open('database_export.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"データエクスポート完了:")
        print(f"- ユーザー: {len(data['users'])}件")
        print(f"- タスク: {len(data['tasks'])}件")
        print(f"- スキル: {len(data['user_skills'])}件")
        print(f"- 設定: {len(data['settings'])}件")
        print(f"ファイル: database_export.json")

if __name__ == "__main__":
    export_data()