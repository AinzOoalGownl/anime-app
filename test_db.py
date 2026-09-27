import psycopg2

url = "postgresql://postgres.nczfbexeexlvbtemqwj:AnimeDB2026Segura@aws-0-us-east-1.pooler.supabase.com:5432/postgres"

try:
    conn = psycopg2.connect(url)
    print("✅ Conexión exitosa")
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM series;")
        total = cur.fetchone()[0]
        print(f"📊 Total de registros en 'series': {total}")
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")