from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from app.config import settings
from app.database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
from app.routes import auth, customer, admin, api

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(customer.router, prefix="/customer", tags=["customer"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(api.router, prefix="/api", tags=["api"])

@app.get("/")
async def root():
    return RedirectResponse(url="/customer")
