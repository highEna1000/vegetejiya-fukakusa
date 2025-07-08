#!/usr/bin/env python3
"""
データベースマイグレーションスクリプト
order_indexとlevelカラムをTaskテーブルに追加
"""
import os
import psycopg
import sqlite3

def migrate_postgresql():
    """PostgreSQL用のマイグレーション"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("DATABASE_URL環境変数が設定されていません。")
        return False
    
    try:
        # PostgreSQLドライバの調整
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        conn = psycopg.connect(database_url)
        cursor = conn.cursor()
        
        # order_indexカラムの追加
        try:
            cursor.execute("ALTER TABLE task ADD COLUMN order_index INTEGER DEFAULT 0")
            print("order_indexカラムを追加しました。")
        except psycopg.errors.DuplicateColumn:
            print("order_indexカラムは既に存在します。")
        except Exception as e:
            print(f"order_index追加でエラー: {e}")
        
        # levelカラムの追加
        try:
            cursor.execute("ALTER TABLE task ADD COLUMN level INTEGER DEFAULT 1")
            print("levelカラムを追加しました。")
        except psycopg.errors.DuplicateColumn:
            print("levelカラムは既に存在します。")
        except Exception as e:
            print(f"level追加でエラー: {e}")
        
        # 既存データの更新
        cursor.execute("UPDATE task SET order_index = 0 WHERE order_index IS NULL")
        cursor.execute("UPDATE task SET level = 1 WHERE level IS NULL")
        
        conn.commit()
        conn.close()
        print("PostgreSQLマイグレーション完了。")
        return True
        
    except Exception as e:
        print(f"PostgreSQLマイグレーションエラー: {e}")
        return False

def migrate_sqlite():
    """SQLite用のマイグレーション"""
    db_path = 'database.db'
    
    if not os.path.exists(db_path):
        print("SQLiteデータベースファイルが見つかりません。")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 既存のカラムをチェック
        cursor.execute("PRAGMA table_info(task)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # order_indexカラムの追加
        if 'order_index' not in columns:
            print("order_indexカラムを追加しています...")
            cursor.execute("ALTER TABLE task ADD COLUMN order_index INTEGER DEFAULT 0")
        else:
            print("order_indexカラムは既に存在します。")
        
        # levelカラムの追加
        if 'level' not in columns:
            print("levelカラムを追加しています...")
            cursor.execute("ALTER TABLE task ADD COLUMN level INTEGER DEFAULT 1")
        else:
            print("levelカラムは既に存在します。")
        
        # 既存データの更新
        cursor.execute("UPDATE task SET order_index = 0 WHERE order_index IS NULL")
        cursor.execute("UPDATE task SET level = 1 WHERE level IS NULL")
        
        conn.commit()
        conn.close()
        print("SQLiteマイグレーション完了。")
        return True
        
    except Exception as e:
        print(f"SQLiteマイグレーションエラー: {e}")
        return False

def migrate_database():
    """環境に応じて適切なマイグレーションを実行"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        print("PostgreSQL環境を検出しました。")
        return migrate_postgresql()
    else:
        print("SQLite環境を検出しました。")
        return migrate_sqlite()

if __name__ == "__main__":
    migrate_database()