# utils.py
from fastapi import FastAPI, Request
from openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import json
from datetime import datetime
import keyword
filePath = 'codehomework.py'
pyresult = ''
import os
templatecheck = 1
api_key = os.getenv("OPENAI_API_KEY")

# สร้าง instance ของ OpenAI client ด้วย API Key
client = OpenAI(api_key=api_key)


memory = ConversationBufferMemory(return_messages=True)
def homework_code_function(data):
    prompt = data.prompt
    file_path = 'codehomework.py'
    
    # แปลงข้อมูล JSON
    try:
        parsed_data = json.loads(prompt)
    except json.JSONDecodeError as e:
        print("Error parsing data:", e)
        return {"error": "Invalid JSON format"}

    # เก็บข้อความใน memory
    homework = parsed_data.get("homework", "")
    code = parsed_data.get("code", "")
    print('homework',homework)
    print('code',code)
    # บันทึกข้อความสุดท้ายใน memory ลงไฟล์
    if code:
        code
        with open(file_path, "wb") as file:
            file.write(code.encode('utf-8'))
    # อ่านโค้ดและทำการวิเคราะห์
    with open(file_path, 'r', encoding='utf-8') as file:
        code_content = file.read()
    # ตรวจสอบว่าเป็นโค้ด Python หรือไม่

    #     # ตรวจสอบผลลัพธ์จาก pylint แล้วกำหนด templatecheck
    #     templatecheck = 4 if pylint_result == "No issues found!" else 2
    #     analysis_response = analyze_and_fix_code_cot(code_content, pylint_result, memory, templatecheck)
    #     return analysis_response
    
    # elif result_compile == "ข้อความธรรมดา":
    #     templatecheck = 1
    #     pylint_result = result_compile
    #     analysis_response = analyze_and_fix_code_cot(code_content, pylint_result, memory, templatecheck)
    #     return analysis_response
    
    # else:
    #     templatecheck = 3
    #     pylint_result = result_compile
    analysis_response = analyze_and_fix_code_cot(code_content, homework,)
    return analysis_response
    
def homework_code_function_help(data):
    homework = data.homework
    prompt = data.prompt
    file_path = 'inputt.py'
    
    # แปลงข้อมูล JSON
    # try:
    #     parsed_data = json.loads(prompt)
    # except json.JSONDecodeError as e:
    #     print("Error parsing data:", e)
    #     return {"error": "Invalid JSON format"}

    # เก็บข้อความใน memory
    for entry in prompt:
        role = entry.role  # เข้าถึง 'role' โดยตรง
        content = entry.content  # เข้าถึง 'content' โดยตรง

        if role == "assistant":
            memory.chat_memory.add_ai_message(content)
        elif role == "user":
            memory.chat_memory.add_user_message(content)

    # บันทึกข้อความสุดท้ายใน memory ลงไฟล์
    if memory.chat_memory.messages:
        last_message = memory.chat_memory.messages[-1].content
        with open(file_path, "wb") as file:
            file.write(last_message.encode('utf-8'))
    with open(file_path, 'r', encoding='utf-8') as file:
        code_content = file.read()
    print(memory.chat_memory.messages[-1].content)
    analysis_response = analyze_and_fix_code_cot2(code_content, memory,homework)
    return analysis_response
   
    
    
    
def run_pylint(filePath):
    try:
        result = subprocess.run(['pylint', filePath], capture_output=True, text=True)
        
        # ตรวจสอบว่ามีข้อความใด ๆ อยู่ใน stdout
        if "Your code has been rated at 10.00/10" in result.stdout:
            pyresult = "No issues found!"
            print(pyresult)
            return "No issues found!"
        else:
            pyresult = result.stdout 
            print(pyresult)
            return result.stdout  # คืนค่า stdout ที่เป็นผลลัพธ์จาก pylint
    except FileNotFoundError:
        print("Error: pylint is not installed.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None  # คืนค่า None ถ้ามีข้อผิดพลาด




def is_python_code(input_text):
     # ลบช่องว่างหัวท้ายและแบ่งข้อความเป็นบรรทัด
    lines = input_text.strip().split('\n')
    
    # ตรวจสอบว่ามีคำสำคัญของ Python หรือไม่
    has_keywords = any(word in input_text for word in keyword.kwlist)
    
    # ตรวจหาสัญลักษณ์ที่มักใช้ในโค้ด Python
    has_syntax_elements = any(char in input_text for char in ['(', ')', ':', '=', '{', '}', '[', ']'])
    
    # ตรวจสอบการเยื้องบรรทัด
    has_indentation = any(line.startswith('    ') for line in lines if line.strip())
    
    # หากไม่พบโครงสร้างใด ๆ ที่เหมือนโค้ด Python ถือว่าเป็น "ข้อความธรรมดา"
    if not (has_keywords or has_syntax_elements or has_indentation):
        return "ข้อความธรรมดา"
    
    # ลอง compile เพื่อดูว่าเป็นโค้ดที่สามารถรันได้หรือไม่
    try:
        compile(input_text, "<string>", "exec")
        return "โค้ดที่ถูกต้อง"
    except (SyntaxError, IndentationError) as e:
        # แสดงรายละเอียดข้อผิดพลาด
        return f"โค้ดที่ผิด: {e.__class__.__name__} - {e}"


def format_and_group_conversations(memory):
    # ปรับรูปแบบประวัติการสนทนาให้มีความชัดเจนและมีบริบทมากขึ้น
    history = [
        f"[{type(msg).__name__}] [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg.content}"
        for msg in memory.chat_memory.messages
    ]
    
    # การจัดกลุ่มข้อความตามบทบาท
    grouped_history = {"user": [], "AI": []}
    for msg in memory.chat_memory.messages:
        role = 'user' if 'HumanMessage' in type(msg).__name__ else 'AI'
        grouped_history[role].append(msg.content)

    return "\n".join(history), grouped_history

def analyze_and_fix_code_cot(code_content, homework ):
    template = """ 
        ดูจากโจทย์ที่ให้ {homework} เเละพิจารณาโค้ดโดยละเอียด {code} ว่าถูกต้องตามโจทย์สั่งรึเปล่าโดยต้องพิจรณาโจทย์โดยละเอียดเเละโค้ดโดยละเอียเพื่อให้คำตอบที่แน่นอน
        ถ้าถูกให้ตอบถูกต้อง ถ้าไม่ถูกตอบไม่ถูกต้อง (ห้ามตอบนอกเหนือจากถูกต้องกับไม่ถูกต้อง)
        """
        
    template2 = """ 
        ดูจากโจทย์ที่ให้ {homework} เเละพิจารณาโค้ดโดยละเอียด {code} ว่าไม่ถูกต้องตามโจทย์ส่วนไหนโดยต้อง
        ให้ใบ้การแก้ไขสั้นๆ(สั้นมากๆ) โดยไม่เฉลยโค้ด
        """
    # system_messages = [
    #     "1. คุณเป็นครูสอน Python ที่ใจดีและให้คำแนะนำเชิงบวกเสมอแถมยังเป็นคนตลกมากๆอีกด้วย",
    #     "2. คุณจะตอบกลับผู้ใช้แบบ Chain of Thought เพื่ออธิบายกระบวนการวิเคราะห์โค้ดอย่างละเอียด",
    #     "3. ให้คำชมเชยการพยายามของผู้ใช้และสร้างความมั่นใจในความสามารถของเขา",
    #     "4. กระตุ้นให้ผู้ใช้คิดวิเคราะห์และเรียนรู้จากข้อผิดพลาดของตนเอง"
    # ]
    # system_message = "\n".join(system_messages)

    print('template')
    print(template)
    # กำหนดค่าลงใน PromptTemplate
    prompt = PromptTemplate(
        input_variables=["code", "homework"], 
        template=template
    )
    prompt_text = prompt.format(
        code=code_content, 
        homework=homework
      
    )

    # สร้างการตอบกลับ
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "คุณคนเชี่ยวชาญภาษา python เเละเป็นคนตรวจข้อสอบโดยละเอียด"},
            {"role": "user", "content": prompt_text},
        ],
    )
    print(response.choices[0].message.content)
    if(response.choices[0].message.content != "ถูกต้อง"):
        prompt = PromptTemplate(
        input_variables=["code", "homework"], 
        template=template2
            )
        prompt_text = prompt.format(
                code=code_content, 
                homework=homework
            
            )
        sy = "คุณคนเชี่ยวชาญภาษา python เเละเป็นคนตรวจข้อสอบโดยละเอียด"
            # สร้างการตอบกลับ
        response = client.chat.completions.create(
        model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content":sy },
                    {"role": "user", "content": prompt_text},
                ],
            )
        return {"response": response.choices[0].message.content}
    else:
        return {"response": response.choices[0].message.content}
        
    
    



def format_and_group_conversations(memory):
    # ปรับรูปแบบประวัติการสนทนาให้มีความชัดเจนและมีบริบทมากขึ้น
    history = [
        f"[{type(msg).__name__}] [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg.content}"
        for msg in memory.chat_memory.messages
    ]
    
    # การจัดกลุ่มข้อความตามบทบาท
    grouped_history = {"user": [], "AI": []}
    for msg in memory.chat_memory.messages:
        role = 'user' if 'HumanMessage' in type(msg).__name__ else 'AI'
        grouped_history[role].append(msg.content)

    return "\n".join(history), grouped_history

def analyze_and_fix_code_cot2(code_content, memory,homework ):
    history, grouped_history = format_and_group_conversations(memory)
    print('history',history)
    print('code_content',code_content)
    print('homework',homework)
    template = """ 
    โจทย์:{homework}
    code:{code}
    ประวัติการสนทนา: {history}
    """
#     system_messages = [
#         "1. คุณเป็นครูสอน Python ที่ใจดีและให้คำแนะนำเชิงบวกเสมอแถมยังเป็นคนตลกมากๆอีกด้วย",
#         "2. คุณจะตอบกลับผู้ใช้แบบ Chain of Thought เพื่ออธิบายกระบวนการวิเคราะห์โค้ดอย่างละเอียด",
#         "3. ให้คำชมเชยการพยายามของผู้ใช้และสร้างความมั่นใจในความสามารถของเขา",
#         "4. กระตุ้นให้ผู้ใช้คิดวิเคราะห์และเรียนรู้จากข้อผิดพลาดของตนเอง"
#     ]
#     system_message = "\n".join(system_messages)

    # กำหนดค่าลงใน PromptTemplate
    prompt = PromptTemplate(
        input_variables=["code", "homework", "history"], 
        template=template
    )
    prompt_text = prompt.format(
        code=code_content, 
        homework=homework, 
        history=history
    )
    # สร้างการตอบกลับ
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "คุณเป็นคนตลกเเละครูสอน python ให้นักเรียนที่พึ่งเริ่มต้นศึกษา python และต้องการให้คุณทำสิ่งต่อไปนี้"},
            {"role": "user", "content": prompt_text},
        ],
    )
    return {"response": response.choices[0].message.content}