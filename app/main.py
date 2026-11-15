from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, dashboard, forms, health, public

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Smart Form Builder backend: dynamic forms, conditional logic, submissions and analytics.",
    debug=settings.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(forms.field_types_router)
app.include_router(forms.router)
app.include_router(public.router)


@app.get("/", tags=["Root"])
def root():
    return {"message": f"Welcome to {settings.APP_NAME}", "docs": "/docs"}
