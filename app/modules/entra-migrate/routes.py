from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core import Module, log
from core.config import settings

from .schemas import Tenant, TenantCreate
from core.utils.sqlite import get_db

router = APIRouter()

@router.get('/')
async def index():
    db = get_db()
    if db:
        print(db)
    return {"message": "Hello World"}

@router.post('/tenant', response_model=TenantCreate)
async def create_tenant(tenant: TenantCreate, db: Session = Depends(get_db)):
    new_tenant = Tenant(**tenant.model_dump())
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)
    return tenant

@router.get('/tenant')
async def get_tenants(db: Session = Depends(get_db)):
    return db.query(Tenant).all()