"""SQLite storage for accounts, posts, reports and connections.

Everything goes through this file, so moving to Supabase/Postgres later means
rewriting only this module. Never store raw passwords here (see auth.py).
"""
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "herhealth.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  alias TEXT UNIQUE NOT NULL,
  salt BLOB NOT NULL,
  pw_hash BLOB NOT NULL,
  role TEXT NOT NULL DEFAULT 'member',            -- member | admin
  status TEXT NOT NULL DEFAULT 'unverified',      -- unverified | pending | verified | rejected
  tag TEXT,                                       -- condition tag claimed, e.g. #PCOS
  doc_name TEXT,
  doc_blob BLOB,                                  -- deleted once a moderator decides
  failed INTEGER NOT NULL DEFAULT 0,
  locked_until REAL NOT NULL DEFAULT 0,
  created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS posts(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  tag TEXT NOT NULL,
  story TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',         -- pending | approved | removed
  created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS reports(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id INTEGER NOT NULL REFERENCES posts(id),
  reporter_id INTEGER NOT NULL REFERENCES users(id),
  open INTEGER NOT NULL DEFAULT 1,
  created REAL NOT NULL,
  UNIQUE(post_id, reporter_id)
);
CREATE TABLE IF NOT EXISTS connections(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  from_id INTEGER NOT NULL REFERENCES users(id),
  to_id INTEGER NOT NULL REFERENCES users(id),
  status TEXT NOT NULL DEFAULT 'pending',         -- pending | accepted | declined
  created REAL NOT NULL,
  UNIQUE(from_id, to_id)
);
"""


@contextmanager
def conn():
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with conn() as c:
        c.executescript(SCHEMA)


def q(sql: str, args=()) -> list:
    with conn() as c:
        return c.execute(sql, args).fetchall()


def one(sql: str, args=()):
    r = q(sql, args)
    return r[0] if r else None


def run(sql: str, args=()) -> int:
    with conn() as c:
        return c.execute(sql, args).lastrowid


# ---- posts -----------------------------------------------------------------
def add_post(user_id: int, tag: str, story: str) -> int:
    return run("INSERT INTO posts(user_id,tag,story,created) VALUES(?,?,?,?)", (user_id, tag, story.strip()[:2000], time.time()))


def approved_posts() -> list:
    return q("SELECT p.*, u.alias FROM posts p JOIN users u ON u.id=p.user_id WHERE p.status='approved' ORDER BY p.created DESC")


def my_posts(user_id: int) -> list:
    return q("SELECT * FROM posts WHERE user_id=? AND status!='removed' ORDER BY created DESC", (user_id,))


def pending_posts() -> list:
    return q("SELECT p.*, u.alias FROM posts p JOIN users u ON u.id=p.user_id WHERE p.status='pending' ORDER BY p.created")


def set_post_status(post_id: int, status: str):
    run("UPDATE posts SET status=? WHERE id=?", (status, post_id))


# ---- reports ---------------------------------------------------------------
def add_report(post_id: int, reporter_id: int) -> bool:
    try:
        run("INSERT INTO reports(post_id,reporter_id,created) VALUES(?,?,?)", (post_id, reporter_id, time.time()))
        return True
    except sqlite3.IntegrityError:
        return False  # already reported by this person


def open_reports() -> list:
    return q("SELECT r.id rid, p.id pid, p.story, p.tag, u.alias FROM reports r JOIN posts p ON p.id=r.post_id "
             "JOIN users u ON u.id=p.user_id WHERE r.open=1 AND p.status!='removed' ORDER BY r.created")


def close_reports(post_id: int):
    run("UPDATE reports SET open=0 WHERE post_id=?", (post_id,))


# ---- connections (consent from both sides, alias only) -----------------------
def request_connection(from_id: int, to_id: int) -> bool:
    if from_id == to_id:
        return False
    if one("SELECT 1 FROM connections WHERE (from_id=? AND to_id=?) OR (from_id=? AND to_id=?)", (from_id, to_id, to_id, from_id)):
        return False
    run("INSERT INTO connections(from_id,to_id,created) VALUES(?,?,?)", (from_id, to_id, time.time()))
    return True


def incoming_requests(user_id: int) -> list:
    return q("SELECT c.id, u.alias FROM connections c JOIN users u ON u.id=c.from_id WHERE c.to_id=? AND c.status='pending'", (user_id,))


def answer_request(conn_id: int, user_id: int, accept: bool):
    run("UPDATE connections SET status=? WHERE id=? AND to_id=?", ("accepted" if accept else "declined", conn_id, user_id))


def connections_of(user_id: int) -> list:
    return q("SELECT u.alias FROM connections c JOIN users u ON u.id=(CASE WHEN c.from_id=? THEN c.to_id ELSE c.from_id END) "
             "WHERE (c.from_id=? OR c.to_id=?) AND c.status='accepted'", (user_id, user_id, user_id))
