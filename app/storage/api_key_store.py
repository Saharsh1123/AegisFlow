from app.db.session import SessionLocal
from sqlalchemy import select
from app.db.models import APIKey
from datetime import datetime
from uuid import UUID


def api_key_to_dict(db_api_key: APIKey):
    return {
        "api_key_id": db_api_key.api_key_id,
        "tenant_id": db_api_key.tenant_id,
        "api_key_name": db_api_key.api_key_name,
        "secret_digest": db_api_key.secret_digest,
        "hmac_key_version": db_api_key.hmac_key_version,
        "created_at": db_api_key.created_at,
        "expires_at": db_api_key.expires_at,
        "revoked_at": db_api_key.revoked_at,
    }


def save_api_key(api_key_data: dict):
    db = SessionLocal()

    try:
        db_api_key = APIKey(**api_key_data)

        db.add(db_api_key)
        db.commit()
        db.refresh(db_api_key)

        return api_key_to_dict(db_api_key)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def get_api_key_by_id(api_key_id: UUID):
    db = SessionLocal()

    try:
        db_api_key = db.get(APIKey, api_key_id)

        if db_api_key is None:
            return None

        return api_key_to_dict(db_api_key)

    finally:
        db.close()


def get_all_api_keys():
    db = SessionLocal()

    try:
        db_api_keys = db.scalars(select(APIKey)).all()

        return [api_key_to_dict(api_key) for api_key in db_api_keys]

    finally:
        db.close()


def revoke_one_api_key(api_key_id: UUID, revoked_at: datetime):
    db = SessionLocal()

    try:
        db_api_key = db.get(APIKey, api_key_id)

        if db_api_key is None:
            return False

        if db_api_key.revoked_at is None:
            db_api_key.revoked_at = revoked_at
            db.commit()
            db.refresh(db_api_key)

        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
