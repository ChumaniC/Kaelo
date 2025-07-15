import json
import os
from datetime import datetime
from dotenv import load_dotenv
from hedera import Client, AccountId, PrivateKey, TopicMessageSubmitTransaction, TopicId
from requests import Session
from backend.models import AuditLog
from database import SessionLocal

# 1. Load .env
load_dotenv()

# 2. Parse our config
ACCOUNT_ID = AccountId.fromString(os.getenv("HEDERA_ACCOUNT_ID"))
PRIVATE_KEY = PrivateKey.fromStringED25519(os.getenv("HEDERA_PRIVATE_KEY"))
TOPIC_ID = TopicId.fromString(os.getenv("HEDERA_TOPIC_ID"))

# 3. Configure the Hedera client
client = Client.forTestnet()
client.setOperator(ACCOUNT_ID, PRIVATE_KEY)


def publish_and_audit(payload: dict, db: Session):
    # 1) Publish to HCS
    response = (
        TopicMessageSubmitTransaction()
        .setTopicId(TOPIC_ID)
        .setMessage(json.dumps(payload))
        .execute(client)
    )
    transaction_id = response.transactionId.toString()

    db = SessionLocal()

    # 2) Persist to the audit_log
    new_audit = AuditLog(
        event_id=payload["eventId"],
        hcs_transaction_id=transaction_id,
        consensus_timestamp=datetime.utcnow(),  # or get from response if available
        payload=payload
    )
    db.add(new_audit)
    db.commit()
    db.close()
    return transaction_id

