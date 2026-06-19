from fastapi import FastAPI
from app.api.routes_events import router
from app.api.routes_tenants import tenant_router

app = FastAPI()

@app.get("/health")
def health():
    return {
            "status": "ok"
           }

app.include_router(router)
app.include_router(tenant_router)