import google.generativeai as genai

# 1. เอา API Key ของคุณมาใส่ตรงนี้เหมือนเดิมครับ
API_KEY = "AIzaSyBKhkuuDuAylH4gLHh8LOuWkpyM9KZF8ik"
genai.configure(api_key=API_KEY)

print("🔍 กำลังสแกนหาชื่อรุ่น AI ที่คุณใช้งานได้...")

# 2. สั่งให้ระบบลิสต์ชื่อรุ่นทั้งหมดออกมา
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
        
print("✅ สแกนเสร็จเรียบร้อย!")