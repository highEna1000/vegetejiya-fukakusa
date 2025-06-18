#!/usr/bin/env python3
"""
データシードスクリプト
開発用のサンプルデータを作成または再作成します
"""
import os
import sys
from app import app, db, User, Task, UserSkill

def reset_database():
    """データベースをリセットして初期状態にする"""
    print("Resetting database...")
    db.drop_all()
    db.create_all()
    print("Database reset completed.")

def create_admin_user():
    """管理者ユーザーを作成"""
    admin = User(username='admin', role='admin', is_first_login=False, order_index=0)
    admin.set_password('password')
    db.session.add(admin)
    print("Admin user created: admin / password")

def create_sample_staff():
    """サンプルスタッフユーザーを作成"""
    staff_users = [
        {'username': 'yamada', 'password': 'yamada123'},
        {'username': 'sato', 'password': 'sato123'},
        {'username': 'tanaka', 'password': 'tanaka123'},
        {'username': 'suzuki', 'password': 'suzuki123'}
    ]
    
    for index, user_data in enumerate(staff_users):
        user = User(
            username=user_data['username'],
            role='staff',
            is_first_login=False,
            order_index=index + 1
        )
        user.set_password(user_data['password'])
        db.session.add(user)
        print(f"Staff user created: {user_data['username']} / {user_data['password']}")

def create_sample_tasks():
    """サンプルタスクを作成"""
    tasks = [
        'レジ打ち',
        '品出し',
        '清掃',
        '発注作業',
        'クレーム対応',
        '在庫管理',
        '接客',
        '商品陳列',
        'POP作成',
        '売上集計'
    ]
    
    for index, task_name in enumerate(tasks):
        task = Task(name=task_name, order_index=index)
        db.session.add(task)
        print(f"Task created: {task_name}")

def create_sample_skills():
    """サンプルスキルデータを作成"""
    import random
    
    users = User.query.all()
    tasks = Task.query.all()
    
    for user in users:
        print(f"Creating skills for {user.username}...")
        for task in tasks:
            # ランダムにスキルを割り当て（管理者は70%、スタッフは40%の確率で「できる」）
            if user.role == 'admin':
                can_do = random.random() < 0.7
            else:
                can_do = random.random() < 0.4
            
            skill = UserSkill(user_id=user.id, task_id=task.id, can_do=can_do)
            db.session.add(skill)

def main():
    """メイン処理"""
    with app.app_context():
        if len(sys.argv) > 1 and sys.argv[1] == '--reset':
            reset_database()
        
        # 既存データをチェック
        if User.query.count() > 0:
            print(f"Existing users: {User.query.count()}")
            print(f"Existing tasks: {Task.query.count()}")
            print("Use --reset flag to reset all data")
            return
        
        try:
            print("Creating sample data...")
            
            # データ作成
            create_admin_user()
            create_sample_staff()
            create_sample_tasks()
            
            # 一度コミットしてIDを取得
            db.session.commit()
            
            # スキルデータを作成
            create_sample_skills()
            
            # 最終コミット
            db.session.commit()
            
            print("\\n=== Sample data created successfully! ===")
            print("Admin user: admin / password")
            print("Staff users:")
            for user in User.query.filter_by(role='staff').all():
                print(f"  {user.username} / {user.username}123")
            
        except Exception as e:
            print(f"Error creating sample data: {e}")
            db.session.rollback()

if __name__ == "__main__":
    main()