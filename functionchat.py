# utils.py
from fastapi import FastAPI, Request
import openai
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import json
from datetime import datetime
import keyword
import os
filePath = 'inputt.py'
pyresult = ''
templatecheck = 1
openai.api_key = os.getenv("OPENAI_API_KEY")

memory = ConversationBufferMemory(return_messages=True)
def process_code_data(data):
    prompt = data.prompt
    file_path = 'inputt.py'
    
    # แปลงข้อมูล JSON
    try:
        parsed_data = json.loads(prompt)
    except json.JSONDecodeError as e:
        print("Error parsing data:", e)
        return {"error": "Invalid JSON format"}

    # เก็บข้อความใน memory
    for entry in parsed_data:
        role = entry.get("role")
        content = entry.get("content", "")
        if role == "assistant": 
            memory.chat_memory.add_ai_message(content)
        elif role == "user":
            memory.chat_memory.add_user_message(content)
    
    # บันทึกข้อความสุดท้ายใน memory ลงไฟล์
    if memory.chat_memory.messages:
        last_message = memory.chat_memory.messages[-1].content
        with open(file_path, "wb") as file:
            file.write(last_message.encode('utf-8'))
    
    # อ่านโค้ดและทำการวิเคราะห์
    with open(file_path, 'r', encoding='utf-8') as file:
        code_content = file.read()
    
    # ตรวจสอบว่าเป็นโค้ด Python หรือไม่
    result_compile = is_python_code(code_content)
    print('Resultcompile:', result_compile)
    
    if result_compile == "โค้ดที่ถูกต้อง": 
        pylint_result = ''
        while pylint_result == '':
            pylint_result = run_pylint(file_path)
            print('pylint_result:', pylint_result)

        # ตรวจสอบผลลัพธ์จาก pylint แล้วกำหนด templatecheck
        templatecheck = 4 if pylint_result == "No issues found!" else 2
        analysis_response = analyze_and_fix_code_cot(code_content, pylint_result, memory, templatecheck)
        return analysis_response
    
    elif result_compile == "ข้อความธรรมดา":
        templatecheck = 1
        pylint_result = result_compile
        analysis_response = analyze_and_fix_code_cot(code_content, pylint_result, memory, templatecheck)
        return analysis_response
    
    else:
        templatecheck = 3
        pylint_result = result_compile
        analysis_response = analyze_and_fix_code_cot(code_content, pylint_result, memory, templatecheck)
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

def analyze_and_fix_code_cot(code_content, pylint_result, memory, templatecheckA):
     # ดึงประวัติการสนทนาและจัดกลุ่ม
    history, grouped_history = format_and_group_conversations(memory)
    print('history',history)
    template = ""
    
    if (templatecheckA == 1):
        template = """ 
                ประวัติการสนทนา AI เเละ USER
        {history}
        user:{code} 
        ตอบคำถามเเละคุยเล่นปกติเชิงให้ความรู้เกี่ยวกับ python
        """
    elif(templatecheckA == 2):
        template = """ 
    กรุณา:
    1.ตรวจว่า {code} ใช้ codepython ไหมหรือเป็นคำถามปกติ
    ถ้าไม่ใช่ codepython ให้คุยเล่นปกติ แต่ถ้าใช่
    ให้แนะนำวิธีแก้ไขตาม {pylint_feedback} หรือถ้าไม่พบปัญหาใน {pylint_feedback} ให้แนะนำต่อว่าโค้ด
    สามารถทำอะไรให้ดีขึ้นได้บ้าง โดยไม่เฉลยโค้ด (นอกจากพบว่าในประวัติการสนทนามีคำว่า 'ยอมแล้ว' หรือ 'เฉลยให้หน่อย' ซึ่งในกรณีนี้ให้เฉลยโค้ดเต็มที่)
    2.ตอบกลับเป็นภาษาไทย

โค้ดหรือคำถาม: 
ประวัติการสนทนา: {history}
    """
    elif(templatecheckA == 3):
        template =  """ 
    กรุณา:
    1.ตรวจว่า {code} ใช้ codepython ไหมหรือเป็นคำถามปกติ
    ถ้าไม่ใช่ codepython ให้คุยเล่นปกติ แต่ถ้าใช่
    ให้แนะนำวิธีแก้ไขตาม {pylint_feedback} หรือถ้าไม่พบปัญหาใน {pylint_feedback} ให้แนะนำต่อว่าโค้ด
    สามารถทำอะไรให้ดีขึ้นได้บ้าง โดยไม่เฉลยโค้ด (นอกจากพบว่าในประวัติการสนทนามีคำว่า 'ยอมแล้ว' หรือ 'เฉลยให้หน่อย' ซึ่งในกรณีนี้ให้เฉลยโค้ดเต็มที่)
    2.ตอบกลับเป็นภาษาไทย

โค้ดหรือคำถาม: {code} 
ประวัติการสนทนา: {history}
    """
    else:
        template = """ 
        เริ่มต้นด้วยการชมเชยว่าคุณทำได้ดีมาก! แล้ววิเคราะห์ว่าโค้ด {code} ของคุณใช้การเขียนที่ดีหรือไม่ เช่น ตัวแปรที่ตั้งไม่มีความหมาย โครงสร้างโค้ดที่ไม่ดี  ทำให้โค้ดสั้นลงเเละเร็วขึ้นได้หรือไม่ และหากพบข้อที่ควรปรับให้คำแนะนำโดยไม่เฉลยคำตอบ 
        ปิดท้ายด้วยคำให้กำลังใจและ Emoji 
        """
    system_messages = [
        "1. คุณเป็นครูสอน Python ที่ใจดีและให้คำแนะนำเชิงบวกเสมอแถมยังเป็นคนตลกมากๆอีกด้วย",
        "2. คุณจะตอบกลับผู้ใช้แบบ Chain of Thought เพื่ออธิบายกระบวนการวิเคราะห์โค้ดอย่างละเอียด",
        "3. ให้คำชมเชยการพยายามของผู้ใช้และสร้างความมั่นใจในความสามารถของเขา",
        "4. กระตุ้นให้ผู้ใช้คิดวิเคราะห์และเรียนรู้จากข้อผิดพลาดของตนเอง"
    ]
    system_message = "\n".join(system_messages)

    print('template')
    print(template)
    print(templatecheckA)
    # กำหนดค่าลงใน PromptTemplate
    prompt = PromptTemplate(
        input_variables=["code", "pylint_feedback", "history"], 
        template=template
    )
    prompt_text = prompt.format(
        code=code_content, 
        pylint_feedback=pylint_result, 
        history=history
    )

    # สร้างการตอบกลับ
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "คุณเป็นคนตลกเเละครูสอน python ให้นักเรียนที่พึ่งเริ่มต้นศึกษา python และต้องการให้คุณทำสิ่งต่อไปนี้"},
            {"role": "user", "content": prompt_text},
        ],
    )
    return {"response": response.choices[0].message['content'].strip()}