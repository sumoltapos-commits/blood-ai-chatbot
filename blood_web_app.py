import streamlit as st
import google.generativeai as genai
import pandas as pd
import time
import os
import datetime

# --- ตั้งค่าหน้าจอ ---
st.set_page_config(page_title="Blood AI Expert", page_icon="🩸", layout="wide")

# --- ระบบ Admin ---
with st.sidebar:
    st.header("⚙️ สำหรับผู้ดูแลระบบ")
    admin_password = st.text_input("🔑 ใส่รหัสผ่าน Admin", type="password")
    
    if admin_password == "54321":
        st.success("✅ ปลดล็อกสิทธิ์ Admin แล้ว")
        
        # 1. อัปโหลดไฟล์ปกติ
        uploaded_files = st.file_uploader("📁 อัปโหลดไฟล์ (PDF, Excel, CSV)", accept_multiple_files=True)
        
        # 2. ข้อมูลจากเว็บไซต์ (ระบบสะสมข้อมูล)
        st.markdown("---")
        st.subheader("🌐 ข้อมูลจากเว็บไซต์ (ระบบสะสม)")
        web_url = st.text_input("🔗 แหล่งอ้างอิง (URL):", "https://thaibloodcentre.redcross.or.th/donor-eligibility/")
        web_date = st.date_input("📅 ข้อมูลวันที่:", datetime.date.today())
        web_text = st.text_area("📝 ก๊อปปี้ข้อความมาวาง (จะถูกเพิ่มต่อท้ายของเดิม):", height=150)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ เพิ่มข้อมูล"):
                if web_text:
                    formatted_date = web_date.strftime("%d/%m/%Y")
                    # ใช้โหมด "a" เพื่อเขียนต่อท้าย และใส่เส้นคั่นให้ AI ดูง่ายขึ้น
                    ref_header = f"\n\n--- ข้อมูลใหม่ ---\nแหล่งอ้างอิง: เว็บไซต์ {web_url} (อัปเดตวันที่ {formatted_date})\n"
                    with open("web_update.txt", "a", encoding="utf-8") as f:
                        f.write(ref_header + web_text + "\n\n====================\n")
                    st.toast("บันทึกข้อมูลเรียบร้อย!")
                else:
                    st.warning("กรุณาใส่ข้อความก่อนกดเพิ่ม")

        with col2:
            # 🆕 ปุ่มล้างข้อมูลทั้งหมด
            if st.button("🗑️ ล้างประวัติเว็บ"):
                if os.path.exists("web_update.txt"):
                    os.remove("web_update.txt")
                    st.toast("ล้างประวัติข้อมูลเว็บทั้งหมดแล้ว")
                else:
                    st.info("ไม่มีประวัติข้อมูลให้ลบ")

        st.markdown("---")
        if st.button("🔄 อัปเดตสมอง AI (รีเซ็ตระบบ)"):
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
        
        # โหลดไฟล์อัปโหลด
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

        # โหลดข้อมูลจากเว็บ (ถ้ามีไฟล์อยู่)
        if os.path.exists("web_update.txt"):
            all_docs.append(genai.upload_file(path="web_update.txt"))
        
        try:
            all_docs.append(genai.upload_file(path="คู่มือการรับบริจาคโลหิต-Blood-Donation-Manual-ปี-2564"))
        except: pass

        time.sleep(5) 

        model = genai.GenerativeModel(model_name='gemini-2.5-flash')
        
        instructions = """คุณคือผู้เชี่ยวชาญการบริจาคโลหิต หน้าที่ของคุณคือตอบคำถามโดยใช้ข้อมูลจากไฟล์ที่ได้รับเท่านั้น
        กฎเหล็ก:
        1. ทุกครั้งที่ตอบ ต้องระบุแหล่งที่มาท้ายประโยคหรือท้ายคำตอบเสมอ
        2. หากใช้ข้อมูลจากส่วนของเว็บไซต์ ให้ระบุ URL และวันที่ที่ระบุไว้ในส่วนหัวของข้อมูลนั้นๆ ให้ชัดเจน
        3. หากหาคำตอบไม่ได้ ให้บอกว่า 'ขออภัยครับ ข้อมูลส่วนนี้ไม่มีในระบบ'
        4. ใช้ภาษาไทยที่สุภาพและเป็นกันเอง"""
        
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
        with st.spinner("🤖 กำลังหาคำตอบ..."):
            try:
                response = st.session_state.chat_session.send_message(user_input)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")