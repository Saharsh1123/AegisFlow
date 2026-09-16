from app.schemas.api_keys import APIKeyCreateRequest
from app.storage import api_key_store, tenant_store
from datetime import datetime, timezone, timedelta
from app.config import API_KEY_HMAC_SECRET_V1
from fastapi import HTTPException
import hashlib
import hmac
import secrets
from uuid import uuid4, UUID

server_hmac_key = API_KEY_HMAC_SECRET_V1.encode("utf-8")


def create_api_key(payload: APIKeyCreateRequest):
    retrieved_tenant = tenant_store.get_tenant_by_id(payload.tenant_id)

    if retrieved_tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if not retrieved_tenant["active"]:
        raise HTTPException(status_code=409, detail="Tenant is inactive")

    new_id = uuid4()

    secret = secrets.token_urlsafe(32)

    message = f"v1:{new_id}:{secret}".encode("utf-8")

    api_key_hmac = hmac.new(server_hmac_key, message, hashlib.sha256)

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=90)

    api_key_persisted = {
        "api_key_id": new_id,
        "tenant_id": payload.tenant_id,
        "api_key_name": payload.api_key_name,
        "secret_digest": api_key_hmac.hexdigest(),
        "hmac_key_version": 1,
        "created_at": now,
        "expires_at": expires_at,
        "revoked_at": None,
    }

    api_key_returned = {
        "api_key": f"agf_{new_id}.{secret}",
        "api_key_id": new_id,
        "tenant_id": payload.tenant_id,
        "api_key_name": payload.api_key_name,
        "created_at": now,
        "expires_at": expires_at,
        "revoked_at": None,
    }

    api_key_store.save_api_key(api_key_persisted)

    return api_key_returned


def get_api_key_by_id(api_key_id: UUID):
    return api_key_store.get_api_key_by_id(api_key_id)


def get_all_api_keys():
    return api_key_store.get_all_api_keys()


def revoke_one_api_key(api_key_id: UUID):
    return api_key_store.revoke_one_api_key(api_key_id, datetime.now(timezone.utc))
