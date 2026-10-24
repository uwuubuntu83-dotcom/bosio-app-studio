import sqlite3, uuid, threading
from datetime import datetime, timezone
from pathlib import Path
DEFAULT_DB="/tmp/bosio.db"; DB_WRITE_LOCK=threading.RLock()
def connect(db_path=None):
    db_path=db_path or DEFAULT_DB; Path(db_path).parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(db_path,check_same_thread=False); c.row_factory=sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON"); return c
def init_db(c):
    c.executescript("""
    CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,name TEXT NOT NULL,prompt TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'created',created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS project_files(id TEXT PRIMARY KEY,project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,path TEXT NOT NULL,content TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,UNIQUE(project_id,path));
    CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY,project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,team TEXT NOT NULL,title TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',attempts INTEGER NOT NULL DEFAULT 0,result TEXT,error TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS cost_records(id TEXT PRIMARY KEY,project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,provider TEXT NOT NULL,model TEXT NOT NULL,amount REAL NOT NULL DEFAULT 0,kind TEXT NOT NULL DEFAULT 'estimate',created_at TEXT NOT NULL);""")
    c.commit()
def now(): return datetime.now(timezone.utc).isoformat()
def new_id(): return uuid.uuid4().hex
