from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from functionchat import run_pylint, is_python_code, format_and_group_conversations, analyze_and_fix_code_cot ,process_code_data
from homework import homework_code_function, homework_code_function_help
import uvicorn
import os

# สร้างแอป FastAPI
app = FastAPI()

# ตั้งค่า CORS Middleware เพื่ออนุญาตให้ทุก Origin เข้าถึง API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# กำหนด Router สำหรับ API
api_router = APIRouter()

# เส้นทาง API พื้นฐาน
@api_router.get("/")
async def read_api_root():
    return {"Hello": "World"}

# เส้นทาง API สำหรับรายการ items
@api_router.get("/items")
async def get_items():
    return {"items": ["item1", "item2"]}

# เส้นทาง API สำหรับการประมวลผลโค้ด
class Prompt(BaseModel):
    prompt: str

# @app.post("/process_code")
# async def process_code(data: Prompt):
#     return homework_code_function(data)

# เส้นทาง API สำหรับ homework
class Message(BaseModel):
    role: str
    content: str

class Promptt(BaseModel):
    homework: str
    prompt: List[Message]

@app.post("/homework_code")
async def homework_code(data: Prompt):
    return homework_code_function(data)

@app.post("/homework_code_help")
async def homework_code(data: Promptt):
   return homework_code_function_help(data)

# รวม Router เข้ากับแอป
app.include_router(api_router, prefix="/api")

# เสิร์ฟ Static Files (สำหรับ Frontend)
app.mount("/assets", StaticFiles(directory="frontend/assets"))

# Route สำหรับเสิร์ฟหน้า Frontend (React หรืออื่นๆ)
@app.get("/{full_path:path}")  # Match ทุกเส้นทางที่ไม่ใช่ API
async def serve_frontend(full_path: str):
    return FileResponse("frontend/index.html")



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # อ่านจาก environment variable PORT
    uvicorn.run(app, host="0.0.0.0", port=port)