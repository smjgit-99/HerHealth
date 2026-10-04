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

-- Community MVP ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS community_profile(
  user_id INTEGER PRIMARY KEY REFERENCES users(id),
  onboarded REAL,                                  -- set when the first-visit modal is saved
  rules_accepted REAL                              -- set when the person accepts the rules to post
);
CREATE TABLE IF NOT EXISTS user_conditions(
  user_id INTEGER NOT NULL REFERENCES users(id),
  condition TEXT NOT NULL,                         -- id from data/conditions.json
  visibility TEXT NOT NULL DEFAULT 'community',    -- community | personal (only the user sees it)
  created REAL NOT NULL,
  PRIMARY KEY(user_id, condition)
);
CREATE TABLE IF NOT EXISTS post_reactions(
  post_id INTEGER NOT NULL REFERENCES posts(id),
  user_id INTEGER NOT NULL REFERENCES users(id),
  kind TEXT NOT NULL,                              -- support | relate | helpful
  created REAL NOT NULL,
  PRIMARY KEY(post_id, user_id, kind)
);
CREATE TABLE IF NOT EXISTS comments(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id INTEGER NOT NULL REFERENCES posts(id),
  user_id INTEGER NOT NULL REFERENCES users(id),
  parent_id INTEGER REFERENCES comments(id),       -- NULL = top level; replies are one level deep
  body TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'visible',          -- visible | removed
  created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS comment_votes(
  comment_id INTEGER NOT NULL REFERENCES comments(id),
  user_id INTEGER NOT NULL REFERENCES users(id),
  created REAL NOT NULL,
  PRIMARY KEY(comment_id, user_id)
);
CREATE TABLE IF NOT EXISTS content_reports(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  target_type TEXT NOT NULL,                       -- post | comment
  target_id INTEGER NOT NULL,
  reporter_id INTEGER NOT NULL REFERENCES users(id),
  reason TEXT NOT NULL,
  open INTEGER NOT NULL DEFAULT 1,
  created REAL NOT NULL,
  UNIQUE(target_type, target_id, reporter_id)
);
"""

# Columns added to the existing posts table (older databases are upgraded in place, nothing is dropped).
POST_COLUMNS = {
    "condition": "TEXT",                          # id from data/conditions.json
    "post_type": "TEXT",                          # Question | Experience | Support needed (optional)
    "anonymous": "INTEGER NOT NULL DEFAULT 0",
    "image": "BLOB",
    "edited": "REAL",
}
# Old posts only had a hashtag; map it so they show up under the right condition.
LEGACY_TAGS = {"#PCOS": "pcos", "#Endometriosis": "endometriosis", "#Fertility": "fertility",
               "#Perimenopause": "menopause", "#Hashimotos": "thyroid", "#Thyroid": "thyroid", "#Anemia": "anemia"}


_ready = False


def _connect():
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init():
    """Create tables and upgrade older databases. Safe to call any number of times."""
    global _ready
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = _connect()
    try:
        c.executescript(SCHEMA)
        have = {r["name"] for r in c.execute("PRAGMA table_info(posts)")}
        for col, ddl in POST_COLUMNS.items():
            if col not in have:
                c.execute(f"ALTER TABLE posts ADD COLUMN {col} {ddl}")
        for tag, cond in LEGACY_TAGS.items():
            c.execute("UPDATE posts SET condition=? WHERE condition IS NULL AND tag=?", (cond, tag))
        c.executescript("""
            CREATE INDEX IF NOT EXISTS ix_posts_cond ON posts(condition, status, created);
            CREATE INDEX IF NOT EXISTS ix_comments_post ON comments(post_id, status);
            CREATE INDEX IF NOT EXISTS ix_react_post ON post_reactions(post_id);
            CREATE INDEX IF NOT EXISTS ix_ucond ON user_conditions(condition, visibility);""")
        c.commit()
    finally:
        c.close()
    _ready = True


@contextmanager
def conn():
    if not _ready:
        init()
    c = _connect()
    try:
        yield c
        c.commit()
    finally:
        c.close()


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


# ============================================================================
# Community MVP
# ============================================================================
DUP_WINDOW = 60  # seconds: an identical post/comment from the same person inside this window is treated as a double click


# ---- profile, conditions, rules --------------------------------------------
def community_profile(user_id: int):
    return one("SELECT * FROM community_profile WHERE user_id=?", (user_id,))


def user_conditions(user_id: int) -> dict:
    """{condition_id: 'community' | 'personal'} in the order they were chosen."""
    return {r["condition"]: r["visibility"] for r in
            q("SELECT condition, visibility FROM user_conditions WHERE user_id=? ORDER BY created, rowid", (user_id,))}


def save_conditions(user_id: int, choices: dict) -> str | None:
    """Replace the person's conditions with `choices` ({id: visibility}) and mark onboarding done.
    Returns an error message or None."""
    if not choices:
        return "Select at least one condition."
    now = time.time()
    with conn() as c:
        c.execute("DELETE FROM user_conditions WHERE user_id=? AND condition NOT IN (%s)" % ",".join("?" * len(choices)),
                  (user_id, *choices))
        for cond, vis in choices.items():
            vis = vis if vis in ("community", "personal") else "community"
            c.execute("INSERT INTO user_conditions(user_id,condition,visibility,created) VALUES(?,?,?,?) "
                      "ON CONFLICT(user_id,condition) DO UPDATE SET visibility=excluded.visibility", (user_id, cond, vis, now))
        c.execute("INSERT INTO community_profile(user_id,onboarded) VALUES(?,?) "
                  "ON CONFLICT(user_id) DO UPDATE SET onboarded=excluded.onboarded", (user_id, now))
    return None


def join_condition(user_id: int, cond: str):
    run("INSERT INTO user_conditions(user_id,condition,visibility,created) VALUES(?,?,'community',?) "
        "ON CONFLICT(user_id,condition) DO UPDATE SET visibility='community'", (user_id, cond, time.time()))


def leave_condition(user_id: int, cond: str) -> bool:
    """Leave a condition. The last remaining condition cannot be removed (returns False)."""
    if len(user_conditions(user_id)) <= 1:
        return False
    run("DELETE FROM user_conditions WHERE user_id=? AND condition=?", (user_id, cond))
    return True


def member_counts() -> dict:
    """Members per condition. Only people who chose 'community' visibility are counted."""
    return {r["condition"]: r["n"] for r in
            q("SELECT condition, COUNT(*) n FROM user_conditions WHERE visibility='community' GROUP BY condition")}


def rules_accepted(user_id: int) -> bool:
    r = community_profile(user_id)
    return bool(r and r["rules_accepted"])


def accept_rules(user_id: int):
    run("INSERT INTO community_profile(user_id,rules_accepted) VALUES(?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET rules_accepted=excluded.rules_accepted", (user_id, time.time()))


# ---- posts -----------------------------------------------------------------
def create_post(user_id: int, condition: str, text: str, post_type, anonymous: bool, image) -> int:
    text = text.strip()[:1500]
    dup = one("SELECT id FROM posts WHERE user_id=? AND condition=? AND story=? AND status='approved' AND created>?",
              (user_id, condition, text, time.time() - DUP_WINDOW))
    if dup:
        return dup["id"]
    return run("INSERT INTO posts(user_id,tag,condition,story,post_type,anonymous,image,status,created) "
               "VALUES(?,?,?,?,?,?,?,'approved',?)",
               (user_id, "#" + condition, condition, text, post_type or None, 1 if anonymous else 0, image, time.time()))


def update_post(post_id: int, user_id: int, text: str, post_type, anonymous: bool) -> bool:
    with conn() as c:
        cur = c.execute("UPDATE posts SET story=?, post_type=?, anonymous=?, edited=? "
                        "WHERE id=? AND user_id=? AND status='approved'",
                        (text.strip()[:1500], post_type or None, 1 if anonymous else 0, time.time(), post_id, user_id))
        return cur.rowcount > 0


def delete_post(post_id: int, user_id: int) -> bool:
    with conn() as c:
        cur = c.execute("UPDATE posts SET status='removed' WHERE id=? AND user_id=?", (post_id, user_id))
        return cur.rowcount > 0


def post_image(post_id: int):
    r = one("SELECT image FROM posts WHERE id=? AND status='approved'", (post_id,))
    return r["image"] if r else None


def _like_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def feed(user_id: int, conditions, search: str = "", sort: str = "latest", limit: int = 10) -> list:
    """Posts for the given condition ids. Never returns the author's id or alias for anonymous posts."""
    if not conditions:
        return []
    where = ["p.status='approved'", "p.condition IN (%s)" % ",".join("?" * len(conditions))]
    args = [user_id, *conditions]
    for word in (search or "").split()[:6]:
        where.append("(p.story LIKE ? ESCAPE '\\' OR IFNULL(p.post_type,'') LIKE ? ESCAPE '\\')")
        args += [f"%{_like_escape(word)}%"] * 2
    order = "(rc + cc) DESC, p.created DESC" if sort == "popular" else "p.created DESC"
    return q(f"""SELECT p.id, p.condition, p.post_type, p.anonymous, p.story, p.created, p.edited,
                        (p.image IS NOT NULL) has_image,
                        (p.user_id = ?) mine,
                        CASE WHEN p.anonymous=1 THEN NULL ELSE u.alias END alias,
                        (SELECT COUNT(*) FROM post_reactions r WHERE r.post_id=p.id) rc,
                        (SELECT COUNT(*) FROM comments c WHERE c.post_id=p.id AND c.status='visible') cc
                 FROM posts p JOIN users u ON u.id=p.user_id
                 WHERE {' AND '.join(where)} ORDER BY {order} LIMIT ?""", (*args, limit))


# ---- reactions -------------------------------------------------------------
def toggle_reaction(post_id: int, user_id: int, kind: str) -> bool:
    """Adds the reaction, or removes it if already there. Returns True when it is now on."""
    with conn() as c:
        cur = c.execute("DELETE FROM post_reactions WHERE post_id=? AND user_id=? AND kind=?", (post_id, user_id, kind))
        if cur.rowcount:
            return False
        c.execute("INSERT INTO post_reactions(post_id,user_id,kind,created) VALUES(?,?,?,?)", (post_id, user_id, kind, time.time()))
        return True


def reaction_summary(post_ids, user_id: int):
    """({post_id: {kind: count}}, {post_id: {kinds the user gave}})"""
    counts, mine = {}, {}
    if not post_ids:
        return counts, mine
    marks = ",".join("?" * len(post_ids))
    for r in q(f"SELECT post_id, kind, COUNT(*) n FROM post_reactions WHERE post_id IN ({marks}) GROUP BY post_id, kind", tuple(post_ids)):
        counts.setdefault(r["post_id"], {})[r["kind"]] = r["n"]
    for r in q(f"SELECT post_id, kind FROM post_reactions WHERE user_id=? AND post_id IN ({marks})", (user_id, *post_ids)):
        mine.setdefault(r["post_id"], set()).add(r["kind"])
    return counts, mine


# ---- comments (one level of replies) --------------------------------------
def add_comment(post_id: int, user_id: int, body: str, parent_id=None):
    """Returns the comment id, or None if the post/parent is not available."""
    body = body.strip()[:500]
    if not body or not one("SELECT 1 FROM posts WHERE id=? AND status='approved'", (post_id,)):
        return None
    if parent_id:
        parent = one("SELECT id, parent_id FROM comments WHERE id=? AND post_id=?", (parent_id, post_id))
        if not parent:
            return None
        parent_id = parent["parent_id"] or parent["id"]   # a reply to a reply stays at the same single level
    dup = one("SELECT id FROM comments WHERE post_id=? AND user_id=? AND body=? AND IFNULL(parent_id,0)=? AND created>?",
              (post_id, user_id, body, parent_id or 0, time.time() - DUP_WINDOW))
    if dup:
        return dup["id"]
    return run("INSERT INTO comments(post_id,user_id,parent_id,body,created) VALUES(?,?,?,?,?)",
               (post_id, user_id, parent_id, body, time.time()))


def comments_for(post_id: int, user_id: int, sort: str = "newest") -> list:
    """Top-level comments (newest or most helpful first), each with a `replies` list (oldest first)."""
    rows = q("""SELECT c.id, c.parent_id, c.body, c.status, c.created, (c.user_id=?) mine,
                       CASE WHEN p.anonymous=1 AND c.user_id=p.user_id THEN NULL ELSE u.alias END alias,
                       (p.anonymous=1 AND c.user_id=p.user_id) is_anon_author,
                       (SELECT COUNT(*) FROM comment_votes v WHERE v.comment_id=c.id) helpful,
                       EXISTS(SELECT 1 FROM comment_votes v WHERE v.comment_id=c.id AND v.user_id=?) i_voted
                FROM comments c JOIN users u ON u.id=c.user_id JOIN posts p ON p.id=c.post_id
                WHERE c.post_id=? ORDER BY c.created""", (user_id, user_id, post_id))
    rows = [dict(r) for r in rows]
    replies = {}
    for r in rows:
        if r["parent_id"]:
            replies.setdefault(r["parent_id"], []).append(r)
    tops = []
    for r in rows:
        if r["parent_id"]:
            continue
        r["replies"] = [x for x in replies.get(r["id"], []) if x["status"] == "visible"]
        if r["status"] == "visible" or r["replies"]:   # a deleted comment stays as a stub only if it has replies
            tops.append(r)
    tops.sort(key=(lambda r: (-r["helpful"], -r["created"])) if sort == "helpful" else (lambda r: -r["created"]))
    return tops


def delete_comment(comment_id: int, user_id: int) -> bool:
    with conn() as c:
        cur = c.execute("UPDATE comments SET status='removed' WHERE id=? AND user_id=?", (comment_id, user_id))
        return cur.rowcount > 0


def toggle_comment_helpful(comment_id: int, user_id: int) -> bool:
    with conn() as c:
        if not c.execute("SELECT 1 FROM comments WHERE id=? AND status='visible'", (comment_id,)).fetchone():
            return False
        cur = c.execute("DELETE FROM comment_votes WHERE comment_id=? AND user_id=?", (comment_id, user_id))
        if cur.rowcount:
            return False
        c.execute("INSERT INTO comment_votes(comment_id,user_id,created) VALUES(?,?,?)", (comment_id, user_id, time.time()))
        return True


# ---- reports (posts and comments) -----------------------------------------
def add_content_report(target_type: str, target_id: int, reporter_id: int, reason: str) -> bool:
    """False if this person already reported the same item."""
    if target_type not in ("post", "comment"):
        return False
    try:
        run("INSERT INTO content_reports(target_type,target_id,reporter_id,reason,created) VALUES(?,?,?,?,?)",
            (target_type, target_id, reporter_id, reason[:80], time.time()))
        return True
    except sqlite3.IntegrityError:
        return False
