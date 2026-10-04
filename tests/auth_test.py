import sys, os
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__))))
from modules import db, auth
db.DB_PATH = __import__("pathlib").Path(__import__("tempfile").gettempdir()) / "hh_test.db"
if db.DB_PATH.exists(): db.DB_PATH.unlink()
os.environ["ADMIN_EMAIL"] = "boss@x.com"
db.init()
u, e = auth.register("A@x.com", "asha_1", "password1"); assert u and not e
assert auth.register("a@x.com", "other", "password1")[1]
assert auth.register("b@x.com", "ab", "password1")[1]
assert auth.register("b@x.com", "bee_1", "short")[1]
b, _ = auth.register("b@x.com", "bee_1", "password2")
adm, _ = auth.register("boss@x.com", "boss", "password3"); assert adm["role"] == "admin"
assert auth.login("a@x.com", "password1")[0]["alias"] == "asha_1"
assert auth.login("nobody@x.com", "x")[1] == auth.BAD_LOGIN
for _ in range(4): assert auth.login("a@x.com", "bad")[1] == auth.BAD_LOGIN
assert "locked" in auth.login("a@x.com", "bad")[1]
assert "Try again" in auth.login("a@x.com", "password1")[1]
assert auth.submit_verification(b["id"], "#PCOS", "x.exe", b"1")
assert auth.submit_verification(b["id"], "#PCOS", "r.pdf", b"%PDF") is None
assert len(auth.pending_verifications()) == 1
auth.decide_verification(b["id"], True)
assert auth.get_user(b["id"])["status"] == "verified" and auth.get_user(b["id"])["doc_blob"] is None
pid = db.add_post(b["id"], "#PCOS", "my story"); assert not db.approved_posts()
db.set_post_status(pid, "approved"); assert len(db.approved_posts()) == 1
assert db.add_report(pid, u["id"]) and not db.add_report(pid, u["id"]); assert len(db.open_reports()) == 1
db.close_reports(pid); assert not db.open_reports()
assert db.request_connection(u["id"], b["id"]) and not db.request_connection(b["id"], u["id"])
r = db.incoming_requests(b["id"]); db.answer_request(r[0]["id"], b["id"], True)
assert db.connections_of(u["id"])[0]["alias"] == "bee_1"
print("db/auth OK")
