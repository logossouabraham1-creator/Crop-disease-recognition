from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.routes.analysis import router as analysis_router


app = FastAPI(
    title="Crop Disease Recognition API",
    description="Backend for our crop health assessment application.",
    version="0.1.0",
)


# Serve CSS, JavaScript, and other static files.
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)


# Load HTML templates.
templates = Jinja2Templates(directory="templates")


# Register the crop image analysis endpoint.
app.include_router(
    analysis_router,
    prefix="/api",
    tags=["Image Analysis"],
)


# Display the homepage.
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )