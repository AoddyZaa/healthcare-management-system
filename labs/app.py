import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials

def run_labs_app():
    columns_order = ["วันที่ตรวจ", "หมวดหมู่", "รายการตรวจ", "ค่าที่วัดได้", "หน่วย", "สถานะ", "แพทย์ผู้สั่งตรวจ", "บันทึกเพิ่มเติม"]
    SPREADSHEET_NAME = "Healthcare_Master_DB"
    SHEET_NAME = "labs"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

    def get_gcp_client():
        try:
            credentials = Credentials.from_service_account_file("appointment2026-3298e4cbba4f.json", scopes=SCOPES)
            return gspread.authorize(credentials)
        except Exception as e:
            st.error(f"❌ Error: {e}")
            return None

    def format_thai_date(date_input):
        try:
            date_str = str(date_input).strip()
            if not date_str or date_str == "nan": return ""
            dt = datetime.strptime(date_str.split('T')[0].strip(), "%Y-%m-%d")
            year_th = dt.year if dt.year > 2500 else dt.year + 543
            month_names = ["", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
            return f"{dt.day} {month_names[dt.month]} {year_th}"
        except: return str(date_input)

    def convert_to_iso_date(date_str):
        try:
            date_str = str(date_str).strip()
            month_map = {"มกราคม": 1, "กุมภาพันธ์": 2, "มีนาคม": 3, "เมษายน": 4, "พฤษภาคม": 5, "มิถุนายน": 6, "กรกฎาคม": 7, "สิงหาคม": 8, "กันยายน": 9, "ตุลาคม": 10, "พฤศจิกายน": 11, "ธันวาคม": 12}
            parts = date_str.split()
            if len(parts) == 3 and parts[1] in month_map:
                year = int(parts[2]) - 543 if int(parts[2]) > 2500 else int(parts[2])
                return datetime(year, month_map[parts[1]], int(parts[0])).strftime("%Y-%m-%d")
            return date_str
        except: return date_str

    def get_data():
        client = get_gcp_client()
        if not client: return pd.DataFrame(columns=columns_order)
        try:
            sh = client.open(SPREADSHEET_NAME)
            sheet = sh.worksheet(SHEET_NAME)
            all_values = sheet.get_all_values()
            if len(all_values) <= 1: return pd.DataFrame(columns=columns_order)
            
            records = []
            for row in all_values[1:]:
                padded = row + [""] * (len(columns_order) - len(row))
                row_data = {
                    "วันที่ตรวจ": format_thai_date(padded[0]),
                    "หมวดหมู่": padded[1],
                    "รายการตรวจ": padded[2],
                    "ค่าที่วัดได้": padded[3],
                    "หน่วย": padded[4],
                    "สถานะ": padded[5],
                    "แพทย์ผู้สั่งตรวจ": padded[6] if len(padded) > 6 else "",
                    "บันทึกเพิ่มเติม": padded[7] if len(padded) > 7 else ""
                }
                records.append(row_data)
                
            return pd.DataFrame(records, columns=columns_order)
        except Exception as e:
            st.error(f"⚠️ โหลดข้อมูล Lab ไม่สำเร็จ: {e}")
            return pd.DataFrame(columns=columns_order)

    def save_data(df):
        client = get_gcp_client()
        if not client: return False
        try:
            df_to_save = df.copy()
            df_to_save['วันที่ตรวจ'] = df_to_save['วันที่ตรวจ'].apply(convert_to_iso_date)
            sh = client.open(SPREADSHEET_NAME)
            sheet = sh.worksheet(SHEET_NAME)
            sheet.clear()
            sheet.update(range_name='A1', values=[columns_order] + df_to_save.astype(str).values.tolist())
            return True
        except Exception as e:
            st.error(f"Error saving: {e}")
            return False

    # ฐานข้อมูล 7 หมวดหมู่หลักแบบดั้งเดิม
    test_database = {
        "1. การทำงานของไต (Kidney Function)": {
            "Blood Urea Nitrogen (BUN)": {"unit": "mg/dL", "min": 6.0, "max": 20.0},
            "Creatinine": {"unit": "mg/dL", "min": 0.70, "max": 1.20},
            "Estimated Glomerular Filtration Rate (eGFR)": {"unit": "mL/min/1.73m²", "min": 60.0, "max": 120.0},
            "Uric Acid": {"unit": "mg/dL", "min": 3.4, "max": 7.0},
        },
        "2. เกลือแร่ในเลือด (Electrolytes)": {
            "Sodium (Na)": {"unit": "mmol/L", "min": 136.0, "max": 145.0},
            "Potassium (K)": {"unit": "mmol/L", "min": 3.5, "max": 5.0},
            "Chloride (Cl)": {"unit": "mmol/L", "min": 98.0, "max": 107.0},
            "Bicarbonate (CO2)": {"unit": "mmol/L", "min": 22.0, "max": 29.0},
            "Calcium (Ca)": {"unit": "mg/dL", "min": 8.5, "max": 10.5},
            "Magnesium (Mg)": {"unit": "mg/dL", "min": 1.7, "max": 2.2},
            "Phosphorus (P)": {"unit": "mg/dL", "min": 2.5, "max": 4.5},
        },
        "3. การทำงานของตับ (Liver Function)": {
            "Total Protein": {"unit": "g/dL", "min": 6.0, "max": 8.3},
            "Albumin": {"unit": "g/dL", "min": 3.5, "max": 5.0},
            "Globulin": {"unit": "g/dL", "min": 2.3, "max": 3.5},
            "Total Bilirubin": {"unit": "mg/dL", "min": 0.2, "max": 1.2},
            "Direct Bilirubin": {"unit": "mg/dL", "min": 0.0, "max": 0.3},
            "Aspartate Aminotransferase (AST / SGOT)": {"unit": "U/L", "min": 0.0, "max": 40.0},
            "Alanine Aminotransferase (ALT / SGPT)": {"unit": "U/L", "min": 0.0, "max": 41.0},
            "Alkaline Phosphatase (ALP)": {"unit": "U/L", "min": 40.0, "max": 129.0},
        },
        "4. ไขมันและเบาหวานในเลือด (Lipid & Glucose)": {
            "Cholesterol (Total)": {"unit": "mg/dL", "min": 0.0, "max": 200.0},
            "Triglycerides": {"unit": "mg/dL", "min": 0.0, "max": 150.0},
            "HDL Cholesterol": {"unit": "mg/dL", "min": 40.0, "max": 60.0},
            "LDL Cholesterol": {"unit": "mg/dL", "min": 0.0, "max": 130.0},
            "Fast Blood Sugar (FBS)": {"unit": "mg/dL", "min": 70.0, "max": 100.0},
            "HbA1c": {"unit": "%", "min": 4.0, "max": 6.0},
        },
        "5. ความสมบูรณ์ของเม็ดเลือด (CBC)": {
            "Hemoglobin (Hb)": {"unit": "g/dL", "min": 12.0, "max": 16.0},
            "Hematocrit (Hct)": {"unit": "%", "min": 36.0, "max": 48.0},
            "White Blood Cell Count (WBC)": {"unit": "cells/cu.mm.", "min": 5000.0, "max": 10000.0},
            "Platelet Count": {"unit": "/cu.mm", "min": 140000.0, "max": 440000.0},
            "Neutrophil": {"unit": "%", "min": 45.0, "max": 74.0},
            "Lymphocyte": {"unit": "%", "min": 16.0, "max": 45.0},
            "Monocyte": {"unit": "%", "min": 4.0, "max": 10.0},
            "Eosinophil": {"unit": "%", "min": 1.0, "max": 7.0},
            "Basophil": {"unit": "%", "min": 0.0, "max": 2.0},
            "MCV": {"unit": "fl", "min": 80.0, "max": 96.0},
            "MCH": {"unit": "pg", "min": 27.0, "max": 32.0},
            "MCHC": {"unit": "gm/dl", "min": 30.0, "max": 35.0},
            "RDW cv": {"unit": "%", "min": 11.6, "max": 14.5},
        },
        "6. ผลตรวจปัสสาวะ (Urinalysis)": {
            "Color": {"unit": "", "min": 0.0, "max": 0.0},
            "Transparency (urine)": {"unit": "", "min": 0.0, "max": 0.0},
            "Specific gravity (urine)": {"unit": "", "min": 1.00, "max": 1.03},
            "pH": {"unit": "", "min": 4.5, "max": 8.0},
            "Glucose (urine)": {"unit": "", "min": 0.0, "max": 0.0},
            "Protein (urine)": {"unit": "", "min": 0.0, "max": 0.0},
            "Blood (urine)": {"unit": "", "min": 0.0, "max": 0.0},
        },
        "7. โรคติดเชื้อและภูมิคุ้มกัน (Serology)": {
            "Hbs Antigen (HBsAg)": {"unit": "", "min": 0.0, "max": 0.0},
        }
    }

    # --- ส่วนรับข้อมูลด้านซ้าย (Sidebar) วางไว้บนสุดเพื่อให้แสดงผลเต็มแถบซ้ายสวยงาม ---
    st.sidebar.header("📝 โหมดบันทึกผลตรวจยกชุด (รายหมวด)")
    check_date = st.sidebar.date_input("📅 วันที่ตรวจ", datetime.now())
    check_time = st.sidebar.time_input("⏰ เวลาตรวจ")
    selected_category = st.sidebar.selectbox("📂 เลือกหมวดหมู่ที่ต้องการป้อน", list(test_database.keys()))
    doc_name = st.sidebar.text_input("🩺 แพทย์ผู้สั่งตรวจ (ถ้ามี)")
    note_val = st.sidebar.text_input("📝 บันทึกเพิ่มเติม")

    st.sidebar.markdown("---")
    st.sidebar.subheader(f"📋 กรอกค่าผลตรวจ: {selected_category}")
    
    batch_inputs = {}
    for test_name, info in test_database[selected_category].items():
        val = st.sidebar.text_input(
            f"{test_name} ({info['unit']})" if info['unit'] else f"{test_name}",
            value="",
            key=f"input_{selected_category}_{test_name}"
        )
        batch_inputs[test_name] = val

    if st.sidebar.button("💾 บันทึกข้อมูลทั้งหมวดหมู่ทีเดียว", type="primary"):
        datetime_str = f"{check_date} {check_time}"
        new_rows = []
        
        for test_name, val in batch_inputs.items():
            if val.strip() != "":
                info = test_database[selected_category][test_name]
                status = "ปกติ"
                try:
                    num_val = float(val)
                    min_v = info["min"]
                    max_v = info["max"]
                    if min_v != max_v:
                        if num_val < min_v:
                            status = "ต่ำ"
                        elif num_val > max_v:
                            status = "ผิดปกติ / สูง"
                except ValueError:
                    if "positive" in val.lower() or "+" in val:
                        status = "ผิดปกติ / สูง"
                    else:
                        status = "ปกติ"
                    
                new_rows.append({
                    "วันที่ตรวจ": datetime_str,
                    "หมวดหมู่": selected_category,
                    "รายการตรวจ": test_name,
                    "ค่าที่วัดได้": val,
                    "หน่วย": info["unit"],
                    "สถานะ": status,
                    "แพทย์ผู้สั่งตรวจ": doc_name,
                    "บันทึกเพิ่มเติม": note_val
                })

        if new_rows:
            df_cur = get_data()
            df_cur['วันที่ตรวจ'] = df_cur['วันที่ตรวจ'].apply(convert_to_iso_date)
            if save_data(pd.concat([df_cur, pd.DataFrame(new_rows)], ignore_index=True)):
                st.sidebar.success(f"บันทึกสำเร็จ {len(new_rows)} รายการ! 🎉")
                st.rerun()
        else:
            st.sidebar.warning("⚠️ กรุณากรอกค่าผลตรวจอย่างน้อย 1 รายการ")

    # --- ส่วนแสดงผลหน้าหลัก (Main Panel) ด้านขวา ---
    st.title("🩺 ระบบบันทึกและวิเคราะห์ผลตรวจสุขภาพ (Medical Lab Tracker)")
    st.markdown("เชื่อมต่อ Google Sheets กลาง: **Healthcare_Master_DB** (Tab: `labs`)")

    df = get_data()

    # --- ส่วนกราฟแสดงผลแนวโน้ม (Plotly Chart) ---
    if not df.empty:
        st.markdown("---")
        st.subheader("📈 กราฟแสดงแนวโน้มผลตรวจสุขภาพตามกาลเวลา")
        
        valid_chart_df = df[df["ค่าที่วัดได้"].str.strip() != ""].copy()
        
        if not valid_chart_df.empty:
            all_recorded_tests = valid_chart_df["รายการตรวจ"].unique().tolist()
            selected_chart_test = st.selectbox("🔍 เลือกรายการตรวจย่อย (เช่น BUN, eGFR, Creatinine) เพื่อดูแนวโน้ม:", all_recorded_tests, key="chart_test_select")

            chart_df = valid_chart_df[valid_chart_df["รายการตรวจ"] == selected_chart_test].copy()
            chart_df["วันที่ตรวจ_dt"] = pd.to_datetime(chart_df["วันที่ตรวจ"], errors="coerce")
            chart_df = chart_df.sort_values("วันที่ตรวจ_dt")

            if len(chart_df) > 0:
                numeric_chart_df = chart_df.copy()
                numeric_chart_df["ค่าตัวเลข"] = pd.to_numeric(numeric_chart_df["ค่าที่วัดได้"].astype(str).str.extract(r'([0-9]+\.?[0-9]*)')[0], errors='coerce')
                numeric_chart_df = numeric_chart_df.dropna(subset=["ค่าตัวเลข"])
                
                if len(numeric_chart_df) > 0:
                    fig = px.line(
                        numeric_chart_df, x="วันที่ตรวจ", y="ค่าตัวเลข", 
                        markers=True, title=f"แนวโน้มผลตรวจ: {selected_chart_test}",
                        labels={"ค่าตัวเลข": "ค่าที่วัดได้", "วันที่ตรวจ": "วันที่ตรวจ"}
                    )
                    fig.update_traces(line=dict(color="#2563eb", width=3), marker=dict(size=8, color="#1d4ed8"))
                    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("ℹ️ รายการนี้เก็บผลลัพธ์เป็นข้อความ จึงไม่แสดงกราฟเส้นตัวเลขครับ")
        else:
            st.info("💡 ยังไม่มีข้อมูลผลตรวจสำหรับแสดงกราฟแนวโน้ม")

    # --- ส่วนตารางข้อมูลย้อนหลัง ---
    st.markdown("---")
    st.subheader("📋 ประวัติการตรวจสุขภาพย้อนหลัง (แก้ไข/ลบได้)")
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="lab_ed_mod")

    if st.button("🔄 อัปเดตและบันทึกข้อมูล Lab ออนไลน์", use_container_width=True, key="lab_up_mod"):
        if save_data(edited_df[columns_order]):
            st.success("อัปเดตข้อมูลลง Google Sheets สำเร็จ!")
            st.rerun()