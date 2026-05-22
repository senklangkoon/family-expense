# 🏠 Family Expense Tracker

แอพบันทึกค่าใช้จ่ายครอบครัว สร้างด้วย Streamlit

## ✅ วิธีติดตั้งและใช้งาน

### 1. ติดตั้ง Python (ถ้ายังไม่มี)
ดาวน์โหลดที่ https://python.org (เลือก Python 3.10+)

### 2. ติดตั้ง dependencies
```bash
pip install -r requirements.txt
```

### 3. รันแอพ
```bash
streamlit run app.py
```

เปิด browser ที่ http://localhost:8501

---

## 🌐 Deploy บน Streamlit Cloud (ฟรี ใช้ได้ทุก device)

1. Push code ขึ้น GitHub
2. ไปที่ https://share.streamlit.io
3. เลือก repo แล้วกด Deploy
4. ได้ URL ที่ทุกคนในครอบครัวเปิดได้เลย!

---

## 📁 โครงสร้างไฟล์

```
family-expense/
├── app.py            ← โค้ดหลัก
├── requirements.txt  ← dependencies
├── expenses.json     ← ข้อมูล (สร้างอัตโนมัติ)
└── uploads/          ← รูปใบเสร็จ (สร้างอัตโนมัติ)
```

---

## ✏️ การแก้ไขเพิ่มเติม

- เพิ่มหมวดหมู่: แก้ที่ตัวแปร `CATEGORIES` ในไฟล์ `app.py`
- เพิ่มฟิลด์ใหม่: เพิ่มใน form และใน record dict
- เปลี่ยนสี: แก้ที่ CSS section ใน `app.py`
