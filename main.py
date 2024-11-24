from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# เสิร์ฟไฟล์ Static (JS, CSS, รูปภาพ ฯลฯ)
app.mount("/static", StaticFiles(directory="frontend/assets"), name="static")

# Route สำหรับเสิร์ฟ index.html
@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")

# ตัวอย่าง API
@app.get("/api")
async def read_root():
    return {"Hello": "World"}
