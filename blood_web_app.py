import streamlit as st
import google.generativeai as genai
import pandas as pd
import time
import os
import datetime # 🚀 เพิ่มไลบรารีจัดการวันที่

# --- ตั้งค่าหน้าจอ ---
st.set_page_config(page_title="Blood AI Expert", page_icon="🩸", layout="wide")

# --- ระบบ Admin ---
with st.sidebar:
    st.header("⚙️ สำหรับผู้ดูแลระบบ")
    admin_password = st.text_input("🔑 ใส่รหัสผ่าน Admin", type="password")
    
    if admin_password == "1234":
        st.success("✅ ปลดล็อกสิทธิ์ Admin แล้ว")
        
        # 1. อัปโหลดไฟล์ปกติ
        uploaded_files = st.file_uploader("📁 อัปโหลดไฟล์ (PDF, Excel, CSV)", accept_multiple_files=True)
        
        # 2. 🆕 อัปเกรดช่องใส่ข้อมูลเว็บ (เพิ่ม URL และ วันที่)
        st.markdown("---")
        st.subheader("🌐 ข้อมูลจากเว็บไซต์")
        
        # ใส่ URL เริ่มต้นไว้ให้เลย
        web_url = st.text_input("🔗 แหล่งอ้างอิง (URL):", "https://thaibloodcentre.redcross.or.th/donor-eligibility/")
        
        # ช่องเลือกวันที่จากปฏิทิน (ค่าเริ่มต้นคือวันปัจจุบัน)
        web_date = st.date_input("📅 ข้อมูลวันที่:", datetime.date.today())
        
        # ช่องวางเนื้อหา
        web_text = st.text_area("📝 ก๊อปปี้ข้อความจากเว็บมาวางที่นี่:", height=200)
        
        if st.button("🔄 อัปเดตสมอง AI (รีเซ็ตระบบ)"):
            # 🆕 เขียนไฟล์ใหม่โดยรวม URL และวันที่เข้าไปด้วย
            if web_text:
                # แปลงวันที่เป็นรูปแบบ วัน/เดือน/ปี
                formatted_date = web_date.strftime("%d/%m/%Y")
                ref_header = f"แหล่งอ้างอิง: เว็บไซต์ {web_url} (ข้อมูลอัปเดตวันที่ {formatted_date})\n\n"
                
                with open("web_update.txt", "w", encoding="utf-8") as f:
                    f.write(ref_header + web_text)
            
            st.session_state.clear()
            st.rerun() 
            
    elif admin_password != "":
        st.error("❌ รหัสผ่านไม่ถูกต้อง")

# --- เตรียม AI & API ---
API_KEY = st.secrets["GEMINI_API_KEY"] 
genai.configure(api_key=API_KEY)

if "chat_session" not in st.session_state:
    with st.spinner("🧠 AI กำลังรวบรวมคัมภีร์ข้อมูล..."):
        all_docs = []
        
        if 'uploaded_files' in locals() and uploaded_files:
            for uploaded_file in uploaded_files:
                file_ext = uploaded_file.name.split('.')[-1].lower()
                if file_ext == 'xlsx':
                    df = pd.read_excel(uploaded_file)
                    csv_name = uploaded_file.name.replace('.xlsx', '.csv')
                    df.to_csv(csv_name, index=False)
                    all_docs.append(genai.upload_file(path=csv_name))
                else:
                    with open(uploaded_file.name, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    all_docs.append(genai.upload_file(path=uploaded_file.name))

        if os.path.exists("web_update.txt"):
            all_docs.append(genai.upload_file(path="web_update.txt"))
        
        try:
            all_docs.append(genai.upload_file(path="คู่มือการรับบริจาคโลหิต-Blood-Donation-Manual-ปี-2564"))
        except: pass

        time.sleep(5) 

        model = genai.GenerativeModel(model_name='gemini-2.5-flash')
        
        # 🆕 ปรับปรุงคำสั่งบังคับให้แสดงแหล่งที่มาตามที่จดไว้ในไฟล์
        instructions = """คุณคือผู้เชี่ยวชาญการบริจาคโลหิต หน้าที่ของคุณคือตอบคำถามโดยใช้ข้อมูลจากไฟล์ที่ได้รับเท่านั้น
        กฎเหล็ก:
        1. ทุกครั้งที่ตอบ ต้องระบุแหล่งที่มาท้ายประโยคหรือท้ายคำตอบเสมอ
        2. หากใช้ข้อมูลจากไฟล์เว็บ (web_update.txt) ให้คัดลอกแหล่งอ้างอิงที่ระบุไว้ส่วนหัวของไฟล์มาแสดงให้ครบถ้วน เช่น [แหล่งที่มา: เว็บไซต์ https://thaibloodcentre.redcross.or.th... (ข้อมูลอัปเดตวันที่ DD/MM/YYYY)]
        3. หากใช้ข้อมูลจากคู่มือ (PDF) ให้บอกว่า [แหล่งที่มา: คู่มือหน้า X]
        4. ถ้าหาคำตอบจากไฟล์ไม่ได้ ให้บอกตามตรงว่า 'ขออภัยครับ ข้อมูลส่วนนี้ไม่มีในระบบ' ห้ามแต่งคำตอบเอง
        5. ใช้ภาษาไทยที่สุภาพ เป็นกันเอง"""
        
        st.session_state.chat_session = model.start_chat(history=[
            {"role": "user", "parts": all_docs + [instructions]}
        ])
        st.session_state.messages = []

# --- หน้าจอถาม-ตอบ ---
st.title("🩸 AI ที่ปรึกษาการบริจาคโลหิต")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if user_input := st.chat_input("พิมพ์คำถามได้เลย..."):
    with st.chat_message("user"): st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("🤖 กำลังเปิดตำราหาคำตอบ..."):
            try:
                response = st.session_state.chat_session.send_message(user_input)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")