from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import uvicorn

app = FastAPI(title="Flight Booking System",version="1.0")

app.mount("/static",StaticFiles(directory="templates",html=True))

# Template folder
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/hello")
async def hello():
    return {"message": "Hello from FastAPI 🚀"}

if __name__=="__main__":
    uvicorn.run(app=app,port=8000,host="0.0.0.0")