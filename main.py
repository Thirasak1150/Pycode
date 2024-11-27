from fastapi import FastAPI, APIRouter,HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from functionchat import run_pylint, is_python_code, format_and_group_conversations, analyze_and_fix_code_cot ,process_code_data
from homework import homework_code_function, homework_code_function_help
import asyncpg
import asyncio
from urllib.parse import urlparse
SQLALCHEMY_DATABASE_URL = "postgresql://pycode_data_m3lo_user:4dxOy3kxWc2cszWvJ3DneIModoofvYuj@dpg-ct2o5pdsvqrc738dsit0-a.oregon-postgres.render.com/pycode_data_m3lo"

# แยกข้อมูลจาก URL
parsed_url = urlparse(SQLALCHEMY_DATABASE_URL)

# ดึงข้อมูลจาก URL
user = parsed_url.username
password = parsed_url.password
host = parsed_url.hostname
port = parsed_url.port or 5432  # พอร์ตสามารถระบุได้หรือใช้พอร์ตเริ่มต้น 5432
database = parsed_url.path[1:]  # เอาชื่อฐานข้อมูลออกจาก path (เริ่มต้นด้วย "/")

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

class Message(BaseModel):
    role: str
    content: str
class UserData(BaseModel):
    email: str
    username: str
    password: str

class Promptt(BaseModel):
    homework: str
    prompt: List[Message]  # ใช้ List สำหรับเก็บ array ของ Message
# เส้นทาง API สำหรับการประมวลผลโค้ด
class Prompt(BaseModel):
    prompt: str

class LoginData(BaseModel):
    email: str
    password: str
async def connect_to_db():
    try:
        conn = await asyncpg.connect(
            user=user,
            password=password,
            database=database,
            host=host,
            port=port
        )
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        raise e
    

    
@app.post("/login/")
async def login(user_data: LoginData):
    # Connect to PostgreSQL database
    
    conn = await connect_to_db()
    
    try:
        # Check if email and password match
        result = await conn.fetchrow(
            'SELECT * FROM "user" WHERE email=$1 AND password=$2',
            user_data.email, user_data.password
        )
        
        if result:
            return {"message": "Loginsuccessful", "user": result}
        else:
             return {"message": "Loginnotsuccess", "user": result}
    
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    finally:
        await conn.close()
@app.post("/add_user")
async def add_user(user_data: UserData):
    conn = await connect_to_db()
    
    try:
        # แทรกข้อมูลลงในฐานข้อมูล
        await conn.execute(
    'INSERT INTO "user"(email, username, password) VALUES($1, $2, $3)',
    user_data.email, user_data.username, user_data.password
)
        return {"message": "User added successfully!"}
    except Exception as e:
        # แสดงข้อผิดพลาดที่เกิดขึ้น
        print(f"Error occurred while adding user: {e}")
        raise HTTPException(status_code=500, detail=f"Error inserting data: {e}")
    finally:
        await conn.close()

# เส้นทาง API พื้นฐาน
@api_router.get("/")
async def read_api_root():
    return {"Hello": "World"}

# เส้นทาง API สำหรับรายการ items
@api_router.get("/items")
async def get_items():
    return {"items": ["item1", "item2"]}


@app.post("/process_code")
async def process_code(data: Prompt):
    return process_code_data(data)

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
