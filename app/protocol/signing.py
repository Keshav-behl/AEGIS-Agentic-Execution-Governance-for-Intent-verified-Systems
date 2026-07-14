import base64
import hashlib
import hmac
import json
import secrets
import sqlite3
import time

from app import config
from app.schemas import ActionProposal


class TokenError(Exception):
    pass


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS used_nonces (
            nonce TEXT PRIMARY KEY,
            used_at REAL NOT NULL
        )
        """
    )
    return conn


def _canonicalize(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _sign(canonical: str) -> str:
    return hmac.new(config.AEGIS_SIGNING_SECRET.encode(), canonical.encode(), hashlib.sha256).hexdigest()


def issue_token(action_proposal: ActionProposal, risk_score: int) -> str:
    payload = {
        "action_proposal": action_proposal.model_dump(),
        "risk_score": risk_score,
        "nonce": secrets.token_hex(16),
        "expires_at": time.time() + config.TOKEN_EXPIRY_SECONDS,
    }
    canonical = _canonicalize(payload)
    signature = _sign(canonical)
    encoded_payload = base64.urlsafe_b64encode(canonical.encode()).decode()
    return f"{encoded_payload}.{signature}"


def verify_token(token: str) -> ActionProposal:
    try:
        encoded_payload, signature = token.rsplit(".", 1)
        canonical = base64.urlsafe_b64decode(encoded_payload.encode()).decode()
    except (ValueError, UnicodeDecodeError) as error:
        raise TokenError("Malformed token") from error

    if not hmac.compare_digest(signature, _sign(canonical)):
        raise TokenError("Invalid signature")

    payload = json.loads(canonical)

    if time.time() > payload["expires_at"]:
        raise TokenError("Token expired")

    conn = _get_conn()
    with conn:
        existing = conn.execute(
            "SELECT 1 FROM used_nonces WHERE nonce = ?", (payload["nonce"],)
        ).fetchone()
        if existing is not None:
            raise TokenError("Token already used (replay detected)")
        conn.execute(
            "INSERT INTO used_nonces (nonce, used_at) VALUES (?, ?)",
            (payload["nonce"], time.time()),
        )

    return ActionProposal.model_validate(payload["action_proposal"])
