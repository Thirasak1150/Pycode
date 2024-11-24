from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# เสิร์ฟไฟล์ Static (JS, CSS, รูปภาพ)
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")

# เสิร์ฟไฟล์ index.html สำหรับเส้นทางหลัก
@app.get("/")
async def serve_index():
    return FileResponse("frontend/index.html")

# เสิร์ฟ index.html สำหรับทุกเส้นทางที่ไม่ใช่ API (เช่น Frontend Routing)
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    return FileResponse("frontend/index.html")
