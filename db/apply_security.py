"""
MahaRainRisk: Apply PostgreSQL Security Hardening & GIN Indexes
Applies Row-Level Security (RLS), creates indices, and configures least-privilege role.
"""

import os
import getpass
import secrets
import psycopg2

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_PATH = os.path.join(BASE_DIR, "db", "security_hardening.sql")

def apply_security():
    db_name = os.getenv("PGDATABASE", "maharainrisk_db")
    db_user = os.getenv("PGUSER", "postgres")
    db_host = os.getenv("PGHOST", "localhost")
    db_port = int(os.getenv("PGPORT", "5432"))
    
    db_pass = os.getenv("PGPASSWORD") or os.getenv("DB_PASSWORD")
    if db_pass is None:
        try:
            print(f"[*] Target Database: {db_user}@{db_host}:{db_port}/{db_name}")
            db_pass = getpass.getpass("Enter PostgreSQL password (characters will not show): ")
        except (KeyboardInterrupt, EOFError):
            print("\n[!] Operation cancelled.")
            return

    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port
        )
        conn.autocommit = True
        cur = conn.cursor()
        print("[*] Connected successfully. Applying security hardening...")

        # 1. Indexes
        print("  - Creating high-performance composite and GIN indexes...")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_weather_taluka_date 
            ON daily_weather (taluka_lgd_code, record_date DESC);
            
            CREATE INDEX IF NOT EXISTS idx_talukas_district 
            ON talukas (district_name);
            
            CREATE INDEX IF NOT EXISTS idx_risk_shap_gin 
            ON taluka_risk_latest USING GIN (shap_summary);
            
            CREATE INDEX IF NOT EXISTS idx_risk_advisory_gin 
            ON taluka_risk_latest USING GIN (bilingual_advisory);
        """)

        # 2. Row Level Security
        print("  - Enabling Row-Level Security (RLS) and read-only policies...")
        cur.execute("""
            ALTER TABLE talukas ENABLE ROW LEVEL SECURITY;
            ALTER TABLE daily_weather ENABLE ROW LEVEL SECURITY;
            ALTER TABLE taluka_risk_latest ENABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS public_read_talukas ON talukas;
            DROP POLICY IF EXISTS public_read_daily_weather ON daily_weather;
            DROP POLICY IF EXISTS public_read_taluka_risk ON taluka_risk_latest;

            CREATE POLICY public_read_talukas ON talukas FOR SELECT USING (true);
            CREATE POLICY public_read_daily_weather ON daily_weather FOR SELECT USING (true);
            CREATE POLICY public_read_taluka_risk ON taluka_risk_latest FOR SELECT USING (true);
        """)

        # 3. Least-privilege Application Role (SEC-05)
        print("  - Configuring least-privilege application role (maharain_app)...")
        app_password = os.getenv("MAHARAIN_APP_PASSWORD") or secrets.token_urlsafe(24)
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'maharain_app') THEN
                    CREATE ROLE maharain_app WITH LOGIN;
                END IF;
            END
            $$;
        """)
        cur.execute("ALTER ROLE maharain_app WITH PASSWORD %s;", (app_password,))
        cur.execute("""
            GRANT CONNECT ON DATABASE maharainrisk_db TO maharain_app;
            GRANT USAGE ON SCHEMA public TO maharain_app;
            GRANT SELECT ON talukas, daily_weather, taluka_risk_latest TO maharain_app;
            REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON talukas, daily_weather, taluka_risk_latest FROM maharain_app;
        """)

        print("\n[SUCCESS] Security Hardening & GIN Indexes Applied Successfully!")
        cur.close()
        conn.close()

    except Exception as e:
        print(f"\n[!] Error applying security hardening: {e}")

if __name__ == "__main__":
    apply_security()

