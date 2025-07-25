# ingestion.py
import os
import time
import json
import base64
from urllib.parse import urljoin

import requests
from datetime import datetime, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.models import AuditLog
from backend.database import SessionLocal

# Mirror-Node REST base URL (Testnet)
MIRROR_HOST = "https://testnet.mirrornode.hedera.com"
API_PREFIX  = "/api/v1"
TOPIC_ID    = os.getenv("HEDERA_TOPIC_ID")
BASE_URL    = f"{MIRROR_HOST}{API_PREFIX}/topics/{TOPIC_ID}/messages"

def lookup_transaction_id(topic_id: str, cons_ts: str) -> str:
    """
    Given a topic ID and consensus_timestamp (e.g. "1752228631.519951000"),
    query /transactions for that exact timestamp and return the transaction_id.
    """
    url = f"{BASE_URL}/transactions"
    params = {
        # look for the consensus‐submit‐message transactions on our topic
        "transactiontype": "CONSENSUSSUBMITMESSAGE",
        "topic.id":        topic_id,
        # Mirror-Node uses the same epoch‐seconds.fraction filter
        "timestamp":       f"eq:{cons_ts}",
        "limit":           1
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    transactions = response.json().get("transactions", [])
    if not transactions:
        return None
    return transactions[0]["transaction_id"]


def ingest_audit_logs():
    """
    Pull new messages from Mirror-Node and write into audit_log.
    Uses the max(consensus_timestamp) in audit_log to only fetch new entries.
    """
    session: Session = SessionLocal()
    try:
        # 1. Find the high-water mark
        last_timestamp = session.query(func.max(AuditLog.consensus_timestamp)).scalar()
        params = {}
        if last_timestamp:
            # get POSIX epoch seconds as a float, then format to 9 decimal places
            epoch = last_timestamp.timestamp()
            # Mirror-Node expects a string like "1651234567.123456789"
            params["timestamp"] = f"lte:{epoch:.9f}"

        url = BASE_URL
        while url:
            url = urljoin(MIRROR_HOST, url)

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            for hcs_message in data["messages"]:
                # Decode and parse
                raw = base64.b64decode(hcs_message["message"]).decode("utf-8")
                payload = json.loads(raw)

                transaction_string= hcs_message["consensus_timestamp"]
                consensus_timestamp = datetime.fromtimestamp(float(transaction_string), tz=timezone.utc)

                # look up the real transaction_id
                # transaction_id = lookup_transaction_id(TOPIC_ID, transaction_string)

                # pull the HCS tx ID from chunk_info
                chunk = hcs_message.get("chunk_info") or hcs_message.get("chunkInfo")
                transaction_id = None
                if isinstance(chunk, dict):
                    transaction_id = chunk.get("initial_transaction_id")

                if not transaction_id:
                    # no way to link on-chain → skip
                    continue

                # insert, skipping if transaction_id already exists
                exists = session.query(AuditLog).filter_by(hcs_transaction_id=transaction_id).first()
                if exists:
                    continue

                # Skip duplicates
                exists = session.query(AuditLog).filter_by(
                    event_id=payload.get("eventId"),
                    consensus_timestamp=consensus_timestamp
                ).first()
                if exists:
                    continue

                # Insert new audit log row
                audit = AuditLog(
                    event_id=payload.get("eventId"),
                    hcs_transaction_id=transaction_id,
                    consensus_timestamp=consensus_timestamp,
                    payload=payload
                )
                session.add(audit)

            session.commit()

            # ─────── Compute next page ───────
            raw_next = data.get("links", {}).get("next")
            if raw_next:
                url = raw_next
            else:
                url = None

            # only the *first* page uses params
            params = None

    finally:
        session.close()


def run_ingestion_loop(poll_interval: int = 30):
    """Continuously ingest on-chain messages every `poll_interval` seconds."""
    # Initial backfill
    ingest_audit_logs()
    # Rolling poll
    while True:
        time.sleep(poll_interval)
        try:
            ingest_audit_logs()
        except Exception as e:
            print(f"[ingestion] error: {e}")
