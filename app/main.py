from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.exceptions import HTTPException
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
from app.routes import auth, customer, admin, api, cashier, reports

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(customer.router, prefix="/customer", tags=["customer"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(api.router, prefix="/api", tags=["api"])
app.include_router(cashier.router, tags=["cashier"])
app.include_router(reports.router, prefix="/admin", tags=["reports"])

@app.exception_handler(HTTPException)
async def auth_exception_handler(request: Request, exc: HTTPException):
    from fastapi.responses import JSONResponse
    if exc.status_code in (401, 403) and not request.url.path.startswith("/api/"):
        return RedirectResponse(url="/auth/login", status_code=302)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.get("/")
async def root():
    return RedirectResponse(url="/customer")
