#!/usr/bin/env python3
"""
データベースマイグレーションスクリプト
order_indexカラムを既存のTaskテーブルに追加
"""
import sqlite3
import os

def migrate_database():
    db_path = 'database.db'
    
    if not os.path.exists(db_path):
        print("データベースファイルが見つかりません。")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # order_indexカラムが存在するかチェック
        cursor.execute("PRAGMA table_info(task)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'order_index' not in columns:
            print("order_indexカラムを追加しています...")
            cursor.execute("ALTER TABLE task ADD COLUMN order_index INTEGER DEFAULT 0")
            
            # 既存のタスクにorder_indexを設定
            cursor.execute("SELECT id FROM task ORDER BY id")
            task_ids = cursor.fetchall()
            
            for index, (task_id,) in enumerate(task_ids):
                cursor.execute("UPDATE task SET order_index = ? WHERE id = ?", (index, task_id))
            
            conn.commit()
            print(f"{len(task_ids)}個のタスクにorder_indexを設定しました。")
        else:
            print("order_indexカラムは既に存在します。")
        
        conn.close()
        print("マイグレーション完了。")
        
    except Exception as e:
        print(f"マイグレーションエラー: {e}")

if __name__ == "__main__":
    migrate_database()