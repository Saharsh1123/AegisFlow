from app.db.session import SessionLocal
from sqlalchemy import select, delete
from app.db.models import Tenant
from uuid import UUID

def tenant_to_dict(db_tenant: Tenant):
    return {
        "tenant_id": db_tenant.tenant_id,
        "tenant_name": db_tenant.tenant_name,
        "active": db_tenant.active,
        "created_at": db_tenant.created_at,
    }


def save_tenant(tenant: dict):
    db = SessionLocal()

    try:
        db_tenant = Tenant(**tenant)

        db.add(db_tenant)
        db.commit()
        db.refresh(db_tenant)

        return tenant_to_dict(db_tenant)
    
    finally:
        db.close()


def get_tenant_by_id(tenant_id: UUID):
    db = SessionLocal()

    try:
        db_tenant = db.get(Tenant, tenant_id)

        if db_tenant is None:
            return None
        
        return tenant_to_dict(db_tenant)
    
    finally:
        db.close()


def get_tenant_by_name(tenant_name: str):
    db = SessionLocal()

    try:
        db_tenant = db.scalar(
            select(Tenant).where(Tenant.tenant_name == tenant_name)
        )

        if db_tenant is None:
            return None

        return tenant_to_dict(db_tenant)

    finally:
        db.close()


def get_all_tenants():
    db = SessionLocal()

    try:
        db_tenants = db.scalars(select(Tenant)).all()

        if db_tenants is None:
            return None
        
        return [tenant_to_dict(tenant) for tenant in db_tenants]

    finally:
        db.close()


def clear_one_tenant(tenant_id: UUID):
    db = SessionLocal()

    try:
        db_tenant = db.get(Tenant, tenant_id)

        if db_tenant is None:
            return False

        db.delete(db_tenant)
        db.commit()

        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def clear_tenants():
    db = SessionLocal()

    try:
        db.execute(delete(Tenant))
        db.commit()

    finally:
        db.close()
