# คู่มือการนำ Web Application ขึ้น Production 🚀

คู่มือนี้จะอธิบายขั้นตอนการนำโปรเจกต์ **AI Laptop Recommender** ขึ้นใช้งานจริงบนคลาวด์โดยใช้บริการฟรีไทร์ (Free Tier) ที่ดีที่สุด

---

## สารบัญ
1. [การนำโค้ดขึ้น GitHub](#1-การนำโค้ดขึ้น-github)
2. [การตั้งค่า Database บน Neon.tech](#2-การตั้งค่า-database-บน-neontech)
3. [การ Deploy Backend (FastAPI) บน Render](#3-การ-deploy-backend-fastapi-บน-render)
4. [การ Deploy Frontend (Next.js) บน Vercel](#4-การ-deploy-frontend-nextjs-บน-vercel)

---

## 1. การนำโค้ดขึ้น GitHub
หากคุณยังไม่ได้นำโค้ดขึ้น GitHub ให้ทำการเปิด Git และ Push ขึ้น Repository ส่วนตัว (Private) หรือสาธารณะ (Public):

```bash
git init
git add .
git commit -m "Prepare project for production"
# สร้าง repository ใน GitHub แล้วทำตามคำสั่งที่ GitHub แนะนำเพื่อ push โค้ดขึ้นไป
```

---

## 2. การตั้งค่า Database บน Neon.tech
เราแนะนำ **Neon.tech** (Serverless Postgres) เนื่องจากสมัครฟรี มีหน้าตาใช้งานง่าย และรองรับ `pgvector` ทันที

1. **สมัครใช้งาน:** ไปที่ [Neon.tech](https://neon.tech/) และสร้างบัญชีใหม่
2. **สร้างโปรเจกต์:** สร้างโปรเจกต์ใหม่ เลือกภูมิภาค (Region) ที่ใกล้ประเทศไทยมากที่สุด (เช่น Singapore หรือ Asia Pacific)
3. **คัดลอก Connection String:** ในหน้า Dashboard ของ Neon คุณจะได้ลิงก์เชื่อมต่อฐานข้อมูล ให้เลือกแบบ `SQLAlchemy` หรือ `URI` และคัดลอกมา เช่น:
   ```text
   postgresql://alex:password@ep-cool-pool-123456.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```
4. **สร้างตารางและย้ายข้อมูล (Run Database Setup Local -> Cloud):**
   เพื่อเปิดใช้งาน `pgvector` และสร้างตาราง `laptops` บน Neon ให้คุณรันคำสั่งบนเครื่องคอมพิวเตอร์ของคุณ โดยการส่ง `DATABASE_URL` ใหม่เข้าไป:
   
   เปิด terminal บนเครื่อง และรันคำสั่งนี้ (เปลี่ยน URI ให้เป็นของคุณ):
   * **สำหรับ Windows (PowerShell):**
     ```powershell
     $env:DATABASE_URL="postgresql://alex:password@ep-cool-pool-123456.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
     python database_setup.py
     ```
   * **รันสคริปต์เพื่อดึงข้อมูลและใส่เวกเตอร์เข้าไปในฐานข้อมูลใหม่บนคลาวด์:**
     *(ตรวจสอบให้แน่ใจว่าได้ระบุ URL คลาวด์ใน ENV แล้ว)*
     ```powershell
     python generate_embeddings.py
     ```
     เมื่อสำเร็จ ข้อมูล Laptops และ AI Embeddings ทั้งหมดจะถูกเก็บไว้บน Neon Cloud อย่างปลอดภัย

---

## 3. การ Deploy Backend (FastAPI) บน Render
[Render.com](https://render.com/) เป็นแพลตฟอร์มที่ยอดเยี่ยมในการโฮสต์ FastAPI Server ฟรี

1. **สมัครใช้งานและเชื่อมต่อ GitHub:** ไปที่ Render และสร้างบัญชีโดยผูกกับ GitHub ของคุณ
2. **สร้าง Web Service ใหม่:**
   * กดปุ่ม **New +** -> **Web Service**
   * เลือก Repository `ai-laptop-recommender` ที่คุณเตรียมไว้
3. **ตั้งค่าคอนฟิกูเรชัน (Configuration):**
   * **Runtime:** `Python`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `uvicorn api:app --host 0.0.0.0 --port $PORT`
   * **Instance Type:** เลือก `Free`
4. **ตั้งค่า Environment Variables:**
   กดปุ่ม **Advanced** -> **Add Environment Variable** และใส่ค่าดังนี้:
   * `DATABASE_URL`: วาง Connection String ของ Neon.tech ที่ก๊อปปี้มาจากข้อ 2
   * `FRONTEND_URL`: (เว้นไว้ก่อน ค่อยกลับมาใส่หลังจากสร้างโปรเจกต์ Vercel ในข้อ 4 เสร็จแล้ว)
5. กด **Create Web Service** และรอระบบทำการ Build (จะใช้เวลาประมาณ 2-5 นาทีในการโหลด AI Model และติดตั้งไลบรารี)
6. เมื่อเสร็จแล้ว คุณจะได้ URL ของหลังบ้านมา เช่น `https://ai-laptop-backend.onrender.com`

---

## 4. การ Deploy Frontend (Next.js) บน Vercel
[Vercel](https://vercel.com/) คือแพลตฟอร์มหลักสำหรับการ Deploy Next.js ที่รวดเร็วและฟรี

1. **สมัครใช้งาน:** ไปที่ Vercel และเข้าสู่ระบบด้วยบัญชี GitHub ของคุณ
2. **สร้างโปรเจกต์ใหม่:**
   * กด **Add New** -> **Project**
   * เลือก Repository `ai-laptop-recommender`
3. **ตั้งค่า Root Directory:**
   * เนื่องจากโปรเจกต์ Next.js ของเราอยู่ในโฟลเดอร์ `frontend` ให้กด **Edit** ข้างๆ **Root Directory** แล้วเลือกโฟลเดอร์ `frontend`
4. **ตั้งค่า Environment Variables:**
   * ในส่วน **Environment Variables** ให้เพิ่มตัวแปรนี้:
     * **Key:** `NEXT_PUBLIC_API_URL`
     * **Value:** ใส่ URL ของ Backend บน Render (เช่น `https://ai-laptop-backend.onrender.com` **ห้ามใส่เครื่องหมาย `/` ปิดท้าย**)
5. กด **Deploy** และรอสักครู่ ระบบจะสร้างหน้าเว็บสำหรับผู้ใช้จริงขึ้นมา
6. คุณจะได้ URL หน้าเว็บมา เช่น `https://ai-laptop-recommender.vercel.app`

---

## 🔒 ขั้นตอนสุดท้าย: เปิดความปลอดภัย CORS
เมื่อคุณได้ URL ของ Frontend จาก Vercel แล้ว ให้กลับไปที่ Render Dashboard ของ Backend:
1. ไปที่แท็บ **Environment** ใน Render
2. แก้ไข/เพิ่ม Environment Variable:
   * **Key:** `FRONTEND_URL`
   * **Value:** ใส่ URL ของหน้าเว็บ Vercel (เช่น `https://ai-laptop-recommender.vercel.app`)
3. บันทึกและรอให้ Backend redeploy อัตโนมัติ

**🎉 ยินดีด้วย! เว็บไซต์ AI Laptop Recommender ของคุณพร้อมใช้งานจริงบนอินเทอร์เน็ตแล้ว!**
