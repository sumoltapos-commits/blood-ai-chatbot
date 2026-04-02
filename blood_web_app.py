import streamlit as st
import google.generativeai as genai
import pandas as pd # 🚀 เพิ่มไลบรารี Pandas สำหรับจัดการ Excel
import time
import os

# ==========================================
# 1. UI Design (หน้าตาแอป)
# ==========================================
st.set_page_config(page_title="Blood AI Expert", page_icon="🩸", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;700&display=swap');
    html, body, [class*="css"], .stMarkdown { font-family: 'Prompt', sans-serif; }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    h1 { color: #D32F2F; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ระบบรักษาความปลอดภัย (Admin Zone)
# ==========================================
uploaded_files = None 

with st.sidebar:
    st.header("⚙️ สำหรับผู้ดูแลระบบ")
    admin_password = st.text_input("🔑 ใส่รหัสผ่าน Admin", type="password")
    
    if admin_password == "123789":
        st.success("✅ ปลดล็อกสิทธิ์ Admin แล้ว")
        # อนุญาตให้อัปโหลดทั้ง PDF และ Excel (xlsx, csv)
        uploaded_files = st.file_uploader("📁 อัปโหลดไฟล์เพิ่มเติม (PDF, Excel, CSV)", accept_multiple_files=True)
        
        if st.button("🔄 อัปเดตสมอง AI (รีเซ็ตระบบ)"):
            st.session_state.clear()
            st.rerun() 
            
    elif admin_password != "":
        st.error("❌ รหัสผ่านไม่ถูกต้อง")

# ==========================================
# 3. เตรียม AI & ไฟล์
# ==========================================
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

if "chat_session" not in st.session_state:
    with st.spinner("🧠 AI กำลังเตรียมข้อมูลในสมอง (อาจใช้เวลาสักครู่)..."):
        all_docs = []
        
        # โหลดไฟล์ที่ Admin อัปโหลดเข้ามาใหม่
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_ext = uploaded_file.name.split('.')[-1].lower()
                
                # 🚀 ถ้านามสกุลเป็น Excel (.xlsx) ให้แปลงเป็น .csv ก่อนส่งให้ AI
                if file_ext == 'xlsx':
                    df = pd.read_excel(uploaded_file)
                    csv_name = uploaded_file.name.replace('.xlsx', '.csv')
                    df.to_csv(csv_name, index=False)
                    doc = genai.upload_file(path=csv_name)
                    all_docs.append(doc)
                    # ลบไฟล์ชั่วคราวทิ้งหลังอัปโหลดเสร็จ
                    os.remove(csv_name)
                    
                # ถ้าเป็น PDF หรือ CSV ปกติ ให้เซฟแล้วอัปโหลดเลย
                else:
                    with open(uploaded_file.name, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    doc = genai.upload_file(path=uploaded_file.name)
                    all_docs.append(doc)
        
        # โหลดไฟล์คู่มือหลักตั้งต้น (ต้องมีไฟล์ manual.pdf อยู่ในโฟลเดอร์)
        try:
            main_pdf = genai.upload_file(path="คู่มือการรับบริจาคโลหิต-Blood-Donation-Manual-ปี-2564.pdf")
            all_docs.append(main_pdf)
        except Exception as e:
            pass

        time.sleep(5) 

        model = genai.GenerativeModel(model_name='gemini-2.5-flash')
        
        instructions = """คุณคือผู้เชี่ยวชาญการบริจาคโลหิต 
        1. ค้นหาข้อมูลจากไฟล์ PDF และข้อมูล CSV ที่อัปโหลดไว้เท่านั้น 
        2. หากเจอข้อมูล ให้สรุปเป็นข้อๆ ให้อ่านง่าย 
        3. ทุกครั้งที่ตอบ ให้ระบุ 'แหล่งที่มา: จากคู่มือหน้า ...' หรือ 'แหล่งที่มา: จากฐานข้อมูล'
        4. ตอบเป็นภาษาไทยที่สุภาพ เป็นกันเอง"""
        
        st.session_state.chat_session = model.start_chat(history=[
            {"role": "user", "parts": all_docs + [instructions]}
        ])
        st.session_state.messages = []

# ==========================================
# 4. หน้าจอถาม-ตอบ
# ==========================================
st.title("🩸 DonorSelect+")
st.caption("สอบถามข้อมูลการบริจาคเลือด อ้างอิงจากฐานข้อมูลและคู่มือที่เชื่อถือได้")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("พิมพ์คำถามเกี่ยวกับการบริจาคเลือดที่นี่..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("🤖 กำลังค้นหาในฐานข้อมูล..."):
            try:
                response = st.session_state.chat_session.send_message(user_input)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")