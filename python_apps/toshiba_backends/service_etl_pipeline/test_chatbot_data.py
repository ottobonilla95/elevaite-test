import psycopg2
from psycopg2.extras import RealDictCursor
import json

def load_config():
    try:
        with open("config/settings.json", "r") as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        print("❌ config/settings.json not found")
        return None

def test_chatbot_data():
    try:
        print("🔍 Testing chatbot data...")
        
        config = load_config()
        if not config:
            return
            
        database_url = config.get("pg_conn_string")
        if not database_url:
            print("❌ pg_conn_string not found in config")
            return
            
        conn = psycopg2.connect(database_url)
        conn.cursor_factory = RealDictCursor
        cur = conn.cursor()
        
        # Test data count
        cur.execute("SELECT COUNT(*) as total FROM chat_data_final")
        count = cur.fetchone()
        print(f"📊 Total chatbot records: {count['total']}")
        
        # Test basic analytics
        cur.execute("""
            SELECT 
                COUNT(DISTINCT session_id) as total_sessions,
                COUNT(*) as total_queries,
                COUNT(*) FILTER (WHERE vote = 1) as thumbs_up,
                COUNT(*) FILTER (WHERE vote = -1) as thumbs_down,
                COUNT(*) FILTER (WHERE vote = 0) as no_vote
            FROM chat_data_final
        """)
        stats = cur.fetchone()
        
        print(f"📈 Sessions: {stats['total_sessions']}")
        print(f"📈 Queries: {stats['total_queries']}")
        print(f"👍 Thumbs up: {stats['thumbs_up']}")
        print(f"👎 Thumbs down: {stats['thumbs_down']}")
        print(f"➖ No vote: {stats['no_vote']}")
        
        # Queries per session
        if stats['total_sessions'] > 0:
            avg_queries = round(stats['total_queries'] / stats['total_sessions'], 2)
            print(f"📊 Average queries per session: {avg_queries}")
        
        # Sample queries
        cur.execute("SELECT request, vote FROM chat_data_final LIMIT 3")
        samples = cur.fetchall()
        print(f"\n🔍 Sample queries:")
        for i, sample in enumerate(samples, 1):
            vote_text = "👍" if sample['vote'] == 1 else "👎" if sample['vote'] == -1 else "➖"
            print(f"   {i}. {sample['request'][:50]}... [{vote_text}]")
        
        cur.close()
        conn.close()
        
        print("🎉 Chatbot data test successful!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chatbot_data()