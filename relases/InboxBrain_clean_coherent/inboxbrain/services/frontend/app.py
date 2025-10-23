import os, json, requests, pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

API_BASE = os.getenv("API_BASE", "http://app:8000")
API_TOKEN = os.getenv("API_TOKEN", "changeme")
DB_DSN = os.getenv("DB_DSN", "mysql+pymysql://app:app@mysql:3306/inboxbrain")
HEADERS = {"x-api-token": API_TOKEN}

st.set_page_config(page_title="InboxBrain Admin", page_icon="📬", layout="wide")

@st.cache_data(ttl=15)
def fetch_api(path: str):
    r = requests.get(f"{API_BASE}{path}", headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()

def post_api(path: str, payload=None):
    r = requests.post(f"{API_BASE}{path}", json=payload or {}, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json() if "application/json" in r.headers.get("content-type","") else {"ok": True}

def put_api(path: str, payload=None):
    r = requests.put(f"{API_BASE}{path}", json=payload or {}, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json() if "application/json" in r.headers.get("content-type","") else {"ok": True}

@st.cache_resource
def get_engine():
    return create_engine(DB_DSN, pool_pre_ping=True)

def df_query(sql: str, params=None):
    eng = get_engine()
    with eng.connect() as cx:
        return pd.read_sql(text(sql), cx, params=params or {})

st.sidebar.title("📬 InboxBrain")
page = st.sidebar.radio("Naviga", ["Dashboard","Emails","Queue","AI Results","Settings","Jobs","Prompt Editor","SQL Console"])
st.sidebar.write("API:", API_BASE)
st.sidebar.write("DB:", DB_DSN)

if page == "Dashboard":
    st.title("📊 Dashboard")
    try:
        total = df_query("SELECT COUNT(*) c FROM emails_raw;")["c"][0]
    except Exception as e:
        total, e = None, e
        st.error(f"DB: {e}")
    try:
        q = df_query("SELECT status, COUNT(*) c FROM email_queue GROUP BY status;")
        qm = {r['status']: int(r['c']) for _, r in q.iterrows()} if not q.empty else {}
    except Exception as e:
        qm = {}
        st.error(f"DB: {e}")
    try:
        ai = df_query("SELECT COUNT(*) c FROM email_ai;")["c"][0]
    except Exception as e:
        ai = None
        st.error(f"DB: {e}")

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Emails", total if total is not None else "—")
    c2.metric("Pending", qm.get("pending",0))
    c3.metric("Error", qm.get("error",0))
    c4.metric("AI rows", ai if ai is not None else "—")

    st.subheader("Ultime 50")
    try:
        df = df_query("""
            SELECT e.id, e.from_address, e.subject, e.received_at, a.intent, a.confidence
            FROM emails_raw e
            LEFT JOIN email_ai a ON a.email_id = e.id
            ORDER BY e.received_at DESC LIMIT 50;
        """)
        st.dataframe(df, use_container_width=True, height=400)
    except Exception as e:
        st.error(str(e))

elif page == "Emails":
    st.title("✉️ Emails")
    limit = st.slider("Righe", 10, 500, 100, step=10)
    intent = st.text_input("Filtro intent")
    sql = """
      SELECT e.id, e.provider, e.mailbox, e.from_address, e.subject, e.received_at,
             LEFT(e.body_text, 500) AS preview, a.intent, a.confidence
      FROM emails_raw e
      LEFT JOIN email_ai a ON a.email_id = e.id
    """
    if intent: sql += " WHERE a.intent=:intent"
    sql += " ORDER BY e.received_at DESC LIMIT :limit"
    try:
        df = df_query(sql, {"limit": limit, "intent": intent})
        st.dataframe(df, use_container_width=True, height=600)
    except Exception as e:
        st.error(str(e))

elif page == "Queue":
    st.title("📦 Queue")
    try:
        df = df_query("""
            SELECT id, email_id, status, attempts, error_msg, updated_at
            FROM email_queue ORDER BY updated_at DESC LIMIT 500;
        """)
        st.dataframe(df, use_container_width=True, height=500)
    except Exception as e:
        st.error(str(e))

    c1,c2,c3 = st.columns(3)
    if c1.button("🔁 Avvia Worker"):
        try:
            st.success(post_api("/admin/run/worker"))
        except Exception as e:
            st.error(str(e))
    if c2.button("📥 Avvia Ingest"):
        try:
            st.success(post_api("/admin/run/ingest"))
        except Exception as e:
            st.error(str(e))
    if c3.button("♻️ Requeue errori"):
        try:
            eng = get_engine()
            with eng.begin() as cx:
                cx.execute(text("UPDATE email_queue SET status='pending', attempts=0 WHERE status='error';"))
            st.success("OK")
        except Exception as e:
            st.error(str(e))

elif page == "AI Results":
    st.title("🤖 AI Results")
    try:
        df = df_query("""
            SELECT a.email_id, a.intent, a.confidence, a.model, a.created_at,
                   e.from_address, e.subject, e.received_at
            FROM email_ai a
            JOIN emails_raw e ON e.id = a.email_id
            ORDER BY a.created_at DESC LIMIT 500;
        """)
        st.dataframe(df, use_container_width=True, height=600)
    except Exception as e:
        st.error(str(e))

elif page == "Settings":
    st.title("⚙️ Settings")
    try:
        df = df_query("SELECT `key`,`value` FROM settings ORDER BY `key`;")
    except Exception as e:
        import pandas as pd
        df = pd.DataFrame(columns=["key","value"])
        st.error(str(e))
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, height=400)
    if st.button("💾 Salva"):
        try:
            payload = {row["key"]: str(row["value"]) for _, row in edited.iterrows() if row["key"]}
            st.success(put_api("/admin/settings", payload))
            st.cache_data.clear()
        except Exception as e:
            st.error(str(e))

elif page == "Jobs":
    st.title("🧰 Jobs")
    c1,c2 = st.columns(2)
    if c1.button("📥 Ingest ora"):
        try:
            st.success(post_api("/admin/run/ingest"))
        except Exception as e:
            st.error(str(e))
    if c2.button("🔁 Worker ora"):
        try:
            st.success(post_api("/admin/run/worker"))
        except Exception as e:
            st.error(str(e))

    st.subheader("Durata media (24h)")
    try:
        df = df_query("""
            SELECT DATE(updated_at) AS d,
                   AVG(TIMESTAMPDIFF(SECOND, created_at, updated_at)) AS avg_sec,
                   COUNT(*) AS jobs
            FROM email_queue
            WHERE updated_at >= NOW() - INTERVAL 1 DAY
              AND status IN ('done','error')
            GROUP BY DATE(updated_at)
            ORDER BY d DESC
            LIMIT 7;
        """)
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.info(str(e))

elif page == "Prompt Editor":
    st.title("🧠 Prompt Editor")
    try:
        df = df_query("SELECT `value` FROM settings WHERE `key`='AI_PROMPT' LIMIT 1;")
        prompt = df["value"][0] if not df.empty else ""
    except Exception as e:
        st.error(str(e)); prompt = ""

    newp = st.text_area("Prompt", value=prompt, height=300)
    if st.button("💾 Salva Prompt"):
        try:
            st.success(put_api("/admin/settings", {"AI_PROMPT": newp}))
        except Exception as e:
            st.error(str(e))

elif page == "SQL Console":
    st.title("🧪 SQL Console")
    sql = st.text_area("SQL", "SELECT * FROM settings LIMIT 10;", height=140)
    if st.button("Esegui"):
        try:
            eng = get_engine()
            with eng.begin() as cx:
                if sql.strip().upper().startswith("SELECT"):
                    df = pd.read_sql(text(sql), cx)
                    st.dataframe(df, use_container_width=True, height=500)
                else:
                    res = cx.execute(text(sql))
                    st.success(f"OK. {res.rowcount} righe.")
        except Exception as e:
            st.error(str(e))
