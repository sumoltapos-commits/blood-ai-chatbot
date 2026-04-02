import google.generativeai as genai
import PyPDF2
import pandas as pd
import io
import time

# ==========================================
# 1. ตั้งค่า API Key และ AI Model (แบบ Paid Plan)
# ==========================================
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

# เมื่อจ่ายเงินแล้ว แนะนำให้ใช้ gemini-1.5-flash เพื่อความเร็วและประหยัด 
# หรือ gemini-1.5-pro ถ้าต้องการความแม่นยำสูงสุดสำหรับตารางซับซ้อน
model = genai.GenerativeModel('gemini-2.5-pro') 

# ==========================================
# 2. ฟังก์ชันดึงข้อความจาก PDF
# ==========================================
def extract_text_from_pdf(pdf_filename, start_page, end_page):
    text = ""
    try:
        with open(pdf_filename, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            actual_end = min(end_page + 1, len(reader.pages))
            for page_num in range(start_page, actual_end):
                page = reader.pages[page_num]
                text += f"--- หน้าที่ {page_num + 1} ---\n"
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการอ่านไฟล์ PDF: {e}")
    return text

# ==========================================
# 3. ฟังก์ชันส่งให้ AI วิเคราะห์ (Prompt แบบเข้มงวด)
# ==========================================
def analyze_with_gemini(raw_text):
    prompt = f"""
    คุณคือผู้เชี่ยวชาญด้านการสกัดข้อมูล (Data Extraction) 
    หน้าที่: เปลี่ยนข้อความจากคู่มือการรับบริจาคโลหิตให้เป็นตาราง CSV
    
    คำสั่งหลัก:
    1. สกัดข้อมูลออกมาเป็นรูปแบบ CSV (Comma Separated Values) เท่านั้น
    2. ต้องมีหัวข้อคอลัมน์ (Header) ที่ชัดเจนในบรรทัดแรก
    3. ห้ามพิมพ์คำอธิบายประกอบ ห้ามมีบทสนทนา ให้พิมพ์มาแค่เนื้อหา CSV เพียวๆ
    4. หากข้อมูลในหน้านั้นไม่มีเนื้อหาที่เป็นเงื่อนไขหรือตาราง ให้ส่งค่าว่างกลับมา
    
    เนื้อหาที่ต้องจัดการ:
    {raw_text}
    """
    response = model.generate_content(prompt)
    return response.text

# ==========================================
# 4. 🚀 ระบบรันอัตโนมัติแบบความเร็วสูง
# ==========================================
def run_high_speed_extraction(pdf_filename, chunk_size=10):
    # ตรวจสอบจำนวนหน้าทั้งหมด
    with open(pdf_filename, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        total_pages = len(reader.pages)
    
    print(f"🚀 เริ่มการสกัดข้อมูลแบบความเร็วสูง (ทั้งหมด {total_pages} หน้า)")
    
    all_chunks = []
    
    for start in range(0, total_pages, chunk_size):
        end = min(start + chunk_size, total_pages)
        print(f"⏳ กำลังประมวลผลหน้าที่ {start + 1} ถึง {end}...")
        
        try:
            # ดึงข้อความ
            raw_text = extract_text_from_pdf(pdf_filename, start, end - 1)
            
            # ส่งให้ AI
            result = analyze_with_gemini(raw_text)
            
            # ล้างโค้ดส่วนเกิน (ถ้ามี)
            clean_csv = result.replace("```csv", "").replace("```", "").strip()
            
            if clean_csv:
                # แปลงเป็น DataFrame ชั่วคราว
                df_chunk = pd.read_csv(io.StringIO(clean_csv))
                all_chunks.append(df_chunk)
                print(f"✅ สำเร็จ (สกัดได้ {len(df_chunk)} แถว)")
            
            # เมื่อผูกบัตรแล้ว พักแค่ 2-3 วินาทีก็พอครับ เพื่อความลื่นไหล
            time.sleep(2)
            
        except Exception as e:
            print(f"⚠️ หน้า {start+1}-{end} พบปัญหาเล็กน้อย: {e}")
            continue

    # รวมผลลัพธ์
    if all_chunks:
        print("\n📦 กำลังรวบรวมข้อมูลทั้งหมดลงไฟล์เดียว...")
        final_df = pd.concat(all_chunks, ignore_index=True)
        
        # ลบแถวที่หัวข้อคอลัมน์ซ้ำ (ถ้ามี)
        final_df = final_df.drop_duplicates().reset_index(drop=True)
        
        output_name = "Blood_Donation_Final_Database.xlsx"
        final_df.to_excel(output_name, index=False)
        print(f"🎉 เสร็จสมบูรณ์! ได้ข้อมูลทั้งหมด {len(final_df)} รายการ")
        print(f"📁 บันทึกไฟล์แล้วที่: {output_name}")
    else:
        print("❌ ไม่สามารถดึงข้อมูลออกมาได้เลย กรุณาตรวจสอบไฟล์ PDF หรือ API Key")

# ==========================================
# 5. เริ่มทำงาน
# ==========================================
# 🚨 ตรวจสอบชื่อไฟล์ให้ถูกต้องนะครับ
PDF_NAME = "คู่มือการรับบริจาคโลหิต-Blood-Donation-Manual-ปี-2564.pdf" 

run_high_speed_extraction(PDF_NAME, chunk_size=10) # อ่านทีละ 10 หน้าเพื่อความแม่นยำ