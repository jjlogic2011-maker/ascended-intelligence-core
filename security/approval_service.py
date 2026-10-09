"""Trusted-backend approval store. Never expose this service to agent code.

verify_human must validate a credential using an independent identity provider
and return an authorized human principal ID. SQLite must reside on trusted
storage. Consumption provides at-most-once dispatch, not exactly-once effects.
"""
import hashlib
import json
import math
import sqlite3
import time
import uuid

from security.shape import ShapeError


def request_digest(request_id, requester_id, action, resource, arguments):
    if not all(isinstance(v, str) and v.strip() for v in
               (request_id, requester_id, action, resource)):
        raise ShapeError("Nonempty request identity and scope required")
    if not isinstance(arguments, dict):
        raise ShapeError("Arguments must be an object")
    try:
        payload = json.dumps([request_id, requester_id, action, resource, arguments],
                             sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (ValueError, TypeError) as exc:
        raise ShapeError("Invalid request arguments") from exc
    return hashlib.sha256(payload.encode()).hexdigest()


class ApprovalService:
    def __init__(self, path, *, verify_human, clock=time.time):
        self.path, self.verify_human, self.clock = str(path), verify_human, clock
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS approvals (
                id TEXT PRIMARY KEY, digest TEXT NOT NULL, approver TEXT NOT NULL,
                issued REAL NOT NULL, expires REAL NOT NULL, status TEXT NOT NULL)""")

    def _connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def issue(self, *, credential, request_id, requester_id, action, resource,
              arguments, ttl=300):
        digest = request_digest(request_id, requester_id, action, resource, arguments)
        approver = self.verify_human(credential, action, resource)
        if not isinstance(approver, str) or not approver.strip() or approver == requester_id:
            raise ShapeError("Authorized distinct human approver required")
        if isinstance(ttl, bool) or not isinstance(ttl, (int, float)) or not math.isfinite(ttl) or not 0 < ttl <= 300:
            raise ShapeError("Approval lifetime must be within 300 seconds")
        now, approval_id = self.clock(), str(uuid.uuid4())
        with self._connect() as db:
            db.execute("INSERT INTO approvals VALUES (?, ?, ?, ?, ?, ?)",
                       (approval_id, digest, approver, now, now + ttl, "approved"))
        return approval_id

    def revoke(self, approval_id):
        with self._connect() as db:
            db.execute("UPDATE approvals SET status='revoked' WHERE id=? AND status='approved'",
                       (approval_id,))

    def consume(self, approval_id, *, request_id, requester_id, action, resource, arguments):
        digest = request_digest(request_id, requester_id, action, resource, arguments)
        now = self.clock()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            result = db.execute("""UPDATE approvals SET status='consumed'
                WHERE id=? AND digest=? AND status='approved' AND issued<=? AND expires>?""",
                                (approval_id, digest, now, now))
            if result.rowcount != 1:
                raise ShapeError("Approval missing, mismatched, expired, revoked or consumed")
            return db.execute("SELECT approver FROM approvals WHERE id=?", (approval_id,)).fetchone()[0]
