import os
import psycopg2
from psycopg2.extras import RealDictCursor


def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS servers (
            guild_id BIGINT PRIMARY KEY,
            channel_id BIGINT,
            report_hour INT DEFAULT 3
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS handles (
            id SERIAL PRIMARY KEY,
            guild_id BIGINT NOT NULL,
            cf_handle TEXT NOT NULL,
            added_by BIGINT,
            UNIQUE(guild_id, cf_handle)
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized.")


def set_channel(guild_id, channel_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO servers (guild_id, channel_id)
        VALUES (%s, %s)
        ON CONFLICT (guild_id) DO UPDATE SET channel_id = EXCLUDED.channel_id
    """, (guild_id, channel_id))
    conn.commit()
    cur.close()
    conn.close()


def set_report_hour(guild_id, hour):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO servers (guild_id, report_hour)
        VALUES (%s, %s)
        ON CONFLICT (guild_id) DO UPDATE SET report_hour = EXCLUDED.report_hour
    """, (guild_id, hour))
    conn.commit()
    cur.close()
    conn.close()


def get_server(guild_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM servers WHERE guild_id = %s", (guild_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def get_all_servers():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM servers WHERE channel_id IS NOT NULL")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def add_handle(guild_id, cf_handle, added_by):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO handles (guild_id, cf_handle, added_by)
            VALUES (%s, %s, %s)
        """, (guild_id, cf_handle, added_by))
        conn.commit()
        return True
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def remove_handle(guild_id, cf_handle):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM handles WHERE guild_id = %s AND LOWER(cf_handle) = LOWER(%s)
    """, (guild_id, cf_handle))
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return deleted > 0


def get_handles(guild_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT cf_handle FROM handles WHERE guild_id = %s ORDER BY cf_handle", (guild_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r["cf_handle"] for r in rows]
