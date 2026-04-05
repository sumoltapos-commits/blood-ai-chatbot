import streamlit as st
import google.generativeai as genai
import pandas as pd
import time
import os
import datetime

# --- ตั้งค่าพื้นฐาน ---
MANUAL_FILE = "คู่มือการรับบริจาคโลหิต-Blood-Donation-Manual-ปี-2564.pdf"
WEB_DB_FILE = "web_database.txt"

st.set_page_config(page_title="Blood AI Expert (Permanent DB)", page_icon="🩸", layout="wide")

# --- ระบบ Admin (จัดการฐานข้อมูล) ---
with st.sidebar:
    st.header("⚙️ ระบบจัดการฐานข้อมูล")
    admin_password = st.text_input("🔑 รหัสผ่าน Admin", type="password")
    
    if admin_password == "1234":
        st.success("สิทธิ์ Admin เปิดใช้งาน")
        
        # 1. เพิ่มข้อมูลจากเว็บไซต์
        st.markdown("---")
        st.subheader("🌐 เพิ่มข้อมูลเข้าคลังความรู้")
        web_url = st.text_input("🔗 URL อ้างอิง:", "https://thaibloodcentre.redcross.or.th/donor-eligibility/")
        web_date = st.date_input("📅 ข้อมูลวันที่:", datetime.date.today())
        web_text = st.text_area("📝 ก๊อปปี้ข้อความมาวางเพื่อสะสม:")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 บันทึกลงคลัง"):
                if web_text:
                    formatted_date = web_date.strftime("%d/%m/%Y")
                    content = f"\n\n--- ข้อมูลอัปเดต ---\nอ้างอิง: {web_url}\nวันที่: {formatted_date}\nเนื้อหา: {web_text}\n"
                    # เขียนลงไฟล์จริงข้างเครื่อง (Append Mode)
                    with open(WEB_DB_FILE, "a", encoding="utf-8") as f:
                        f.write(content)
                    st.toast("บันทึกเข้าคลังถาวรแล้ว!")
                else:
                    st.warning("กรุณาใส่ข้อความ")

        with col2:
            if st.button("🗑️ ล้างคลังเว็บ"):
                if os.path.exists(WEB_DB_FILE):
                    os.remove(WEB_DB_FILE)
                    st.toast("ล้างคลังความรู้สะสมแล้ว")
                else:
                    st.info("คลังว่างเปล่า")

        # 2. อัปโหลดไฟล์เสริมอื่นๆ (ถ้ามี)
        st.markdown("---")
        st.subheader("📁 อัปโหลดไฟล์เสริม (.pdf, .xlsx)")
        uploaded_files = st.file_uploader("เลือกไฟล์", accept_multiple_files=True)
        
        if st.button("🔄 อัปเดตสมอง AI (Re-index)"):
            st.session_state.clear()
            st.rerun()

    elif admin_password != "":
        st.error("รหัสไม่ถูกต้อง")

# --- เตรียม AI & ฐานข้อมูล (จะถูกเรียกทุกครั้งที่เริ่ม Session ใหม่) ---
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

if "chat_session" not in st.session_state:
    with st.spinner("🧠 AI กำลังโหลดคลังความรู้ถาวร..."):
        all_docs = []
        
        # ส่วนที่ 1: โหลดคู่มือปี 2564 (ไฟล์บังคับ)
        if os.path.exists(MANUAL_FILE):
            all_docs.append(genai.upload_file(path=MANUAL_FILE))
        else:
            st.error(f"❌ ไม่พบไฟล์ {MANUAL_FILE} ในโฟลเดอร์โปรเจกต์!")

        # ส่วนที่ 2: โหลดคลังความรู้สะสมจากเว็บ (ถ้ามี)
        if os.path.exists(WEB_DB_FILE):
            all_docs.append(genai.upload_file(path=WEB_DB_FILE))

        # ส่วนที่ 3: โหลดไฟล์ที่ Admin เพิ่งอัปโหลด (ถ้ามี)
        if 'uploaded_files' in locals() and uploaded_files:
            for f in uploaded_files:
                with open(f.name, "wb") as temp_f:
                    temp_f.write(f.getbuffer())
                all_docs.append(genai.upload_file(path=f.name))

        time.sleep(5) # รอ Google ประมวลผลไฟล์

        model = genai.GenerativeModel(model_name='gemini-2.5-flash')
        
        instructions = f"""คุณคือผู้เชี่ยวชาญการบริจาคโลหิตของสภากาชาดไทย 
        ใช้ข้อมูลจากไฟล์หลัก {MANUAL_FILE} และคลังความรู้สะสมจากเว็บที่ได้รับเท่านั้น
        กฎเหล็ก:
        1. ต้องระบุแหล่งที่มาท้ายคำตอบเสมอ (เช่น [อ้างอิง: คู่มือหน้า X] หรือ [อ้างอิง: เว็บไซต์... วันที่...])
        2. หากหาไม่เจอ ให้ตอบว่าไม่ทราบ อย่าเดา
        3. ตอบเป็นภาษาไทยที่สุภาพและกระชับ"""
        
        st.session_state.chat_session = model.start_chat(history=[
            {"role": "user", "parts": all_docs + [instructions]}
        ])
        st.session_state.messages = []

# --- หน้าจอสนทนา ---
st.title("🩸 Blood Donation AI Expert")
st.caption("ฐานข้อมูลหลัก: คู่มือปี 2564 + คลังความรู้สะสมสภากาชาด")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if user_input := st.chat_input("สอบถามเรื่องการบริจาคเลือดที่นี่..."):
    with st.chat_message("user"): st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("🔍 กำลังค้นหาคลังความรู้..."):
            try:
                response = st.session_state.chat_session.send_message(user_input)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")