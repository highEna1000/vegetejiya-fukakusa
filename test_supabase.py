#!/usr/bin/env python3
"""
Supabase接続テストスクリプト
"""
import os
import psycopg

def test_supabase_connection():
    """Supabaseへの接続をテスト"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL環境変数が設定されていません")
        print("以下を実行してください:")
        print("export DATABASE_URL='postgresql://postgres:vegetejiya1000@db.tulxuuvrprszmofnrxyl.supabase.co:5432/postgres'")
        return False
    
    try:
        print("🔄 Supabaseに接続しています...")
        
        # PostgreSQLドライバの調整
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        conn = psycopg.connect(database_url)
        cursor = conn.cursor()
        
        # 基本的な接続テスト
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✅ 接続成功！")
        print(f"📊 PostgreSQLバージョン: {version}")
        
        # 既存テーブルの確認
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"📋 既存テーブル: {[table[0] for table in tables]}")
        else:
            print("📋 テーブルなし（新規データベース）")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 接続エラー: {e}")
        print("\n💡 トラブルシューティング:")
        print("1. パスワードが正しいか確認")
        print("2. 接続文字列が正しいか確認")
        print("3. Supabaseプロジェクトが起動しているか確認")
        return False

if __name__ == "__main__":
    test_supabase_connection()