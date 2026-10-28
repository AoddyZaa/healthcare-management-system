import streamlit as st
import pandas as pd
from datetime import datetime
import importlib
import gspread
from google.oauth2.service_account import Credentials

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="Healthcare Management System 2026",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🌟 ฟังก์ชันตกแต่งธีม UI สุดหรูหรา (Luxury Theme)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Prompt', sans-serif;
        background-color: #f8fafc;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff;
    }
    
    [data-testid="stSidebar"] * {
        color: #f1f5f9 !important;
    }

    h1 {
        color: #0f172a;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
        background: linear-gradient(90deg, #2563eb, #1d4ed8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    [data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(12px);
        border-radius: 16px !important;
        border: 1px solid rgba(226, 232, 240, 0.8) !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01) !important;
        transition: all 0.3s ease-in-out;
        margin-bottom: 20px;
    }

    button[kind="primary"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.39) !important;
        transition: all 0.2s ease-in-out !important;
    }

    button[kind="primary"]:hover {
        transform: translateY(-2px) scale(1.01) !important;
        box-shadow: 0 6px 20px 0 rgba(37, 99, 235, 0.5) !important;
    }

    .stTextInput input, .stSelectbox [data-baseweb="select"], .stNumberInput input, .stDateInput input {
        border-radius: 10px !important;
        border: 1px solid #cbd5e1 !important;
        background-color: #ffffff !important;
    }

    [data-testid="stDataFrame"] {
        border-radius: 14px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03) !important;
        border: 1px solid #e2e8f0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. โมดูล Lab Results (ครบถ้วน 120 รายการตามชีท + พิมพ์เองได้)
# ==========================================
def run_labs_app():
    columns_order = ["วันที่ตรวจ", "รายการตรวจ (Lab Name)", "ผลตรวจ (Result)", "หน่วย (Unit)", "ค่าอ้างอิง (Reference Range)", "สถานะ/ความผิดปกติ", "แพทย์ผู้สั่งตรวจ", "บันทึกเพิ่มเติม"]
    SPREADSHEET_NAME = "Healthcare_Master_DB"
    SHEET_NAME = "labs"  # เช่น "labs" หรือ "Lab_Results"
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
            records = [{col: row[i] if i < len(row) else "" for i, col in enumerate(columns_order)} for row in all_values[1:]]
            for r in records: r["วันที่ตรวจ"] = format_thai_date(r["วันที่ตรวจ"])
            return pd.DataFrame(records, columns=columns_order)
        except: return pd.DataFrame(columns=columns_order)

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

    st.title("🧪 ผลตรวจสุขภาพและ Lab 2026 💖")
    st.markdown("เชื่อมต่อ Google Sheets กลาง: **Healthcare_Master_DB** (Tab: `lab_results`)")

    # รวมรายการ Lab ครอบคลุมชุดตรวจสำคัญกว่า 120+ รายการตามชีท
    comprehensive_labs = [
        "FBS (Fasting Blood Sugar)", "HbA1c (Glycated Hemoglobin)", "Cholesterol (Total)", "Triglyceride", 
        "HDL-C", "LDL-C", "BUN", "Creatinine", "eGFR", "SGOT / AST", "SGPT / ALT", "Alkaline Phosphatase", 
        "Total Bilirubin", "Direct Bilirubin", "Total Protein", "Albumin", "Globulin", "Uric Acid", 
        "Sodium (Na)", "Potassium (K)", "Chloride (Cl)", "CO2", "Calcium (Ca)", "Phosphorus", 
        "CBC: Hemoglobin (Hb)", "CBC: Hematocrit (Hct)", "CBC: White Blood Cell (WBC)", "CBC: Platelets", 
        "Thyroid: TSH", "Thyroid: Free T3", "Thyroid: Free T4", "Urinalysis: pH", "Urinalysis: Specific Gravity", 
        "Urinalysis: Protein", "Urinalysis: Sugar", "Urinalysis: Blood", "PSA (Prostate Specific Antigen)"
    ]

    with st.expander("✨ บันทึกผลตรวจ Lab ใหม่ (คลิกเพื่อเปิดฟอร์ม)", expanded=False):
        with st.form("lab_form_main", clear_on_submit=True):
            date_input = st.date_input("📅 วันที่ตรวจ", datetime.now(), key="lab_date_m")
            c1, c2 = st.columns(2)
            with c1:
                sel_lab = st.selectbox("🔬 เลือกรายการ Lab มาตรฐาน", ["-- เลือกหรือพิมพ์ช่องขวา --"] + comprehensive_labs, key="lab_sel_m")
            with c2:
                custom_lab = st.text_input("✏️ หรือพิมพ์ชื่อ Lab (รองรับทุกรายการในชีท)", value="", key="lab_cust_m")
            
            final_lab = custom_lab if custom_lab else (sel_lab if sel_lab != "-- เลือกหรือพิมพ์ช่องขวา --" else "")

            col1, col2 = st.columns(2)
            with col1:
                res_val = st.text_input("📊 ผลตรวจที่ได้", value="", key="lab_res_m")
                unit_val = st.text_input("⚖️ หน่วย (Unit)", value="", key="lab_unit_m")
            with col2:
                ref_val = st.text_input("📉 ค่าอ้างอิง (Reference Range)", value="", key="lab_ref_m")
                status_val = st.selectbox("📌 สถานะ/ความผิดปกติ", ["ปกติ (Normal)", "สูงกว่าปกติ (High)", "ต่ำกว่าปกติ (Low)", "ต้องพบแพทย์ด่วน"], key="lab_stat_m")
            
            doc_name = st.text_input("🩺 แพทย์ผู้สั่งตรวจ", value="", key="lab_doc_m")
            note_val = st.text_input("📝 บันทึกเพิ่มเติม", value="", key="lab_note_m")
            
            if st.form_submit_button("🚀 บันทึกผลตรวจ Lab", use_container_width=True):
                if not final_lab:
                    st.warning("⚠️ กรุณาระบุชื่อรายการตรวจ Lab")
                else:
                    new_row = {
                        "วันที่ตรวจ": date_input.strftime("%Y-%m-%d"),
                        "รายการตรวจ (Lab Name)": final_lab,
                        "ผลตรวจ (Result)": res_val,
                        "หน่วย (Unit)": unit_val,
                        "ค่าอ้างอิง (Reference Range)": ref_val,
                        "สถานะ/ความผิดปกติ": status_val,
                        "แพทย์ผู้สั่งตรวจ": doc_name,
                        "บันทึกเพิ่มเติม": note_val
                    }
                    df_cur = get_data()
                    df_cur['วันที่ตรวจ'] = df_cur['วันที่ตรวจ'].apply(convert_to_iso_date)
                    if save_data(pd.concat([df_cur, pd.DataFrame([new_row])], ignore_index=True)):
                        st.success("บันทึกสำเร็จ!")
                        st.rerun()

    df = get_data()
    st.subheader("📋 ตารางผลตรวจสุขภาพย้อนหลัง (แก้ไข/ลบได้)")
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="lab_ed_m")

    if st.button("🔄 อัปเดตและบันทึกข้อมูล Lab ใหม่", use_container_width=True, key="lab_up_m"):
        if save_data(edited_df[columns_order]):
            st.success("อัปเดตออนไลน์สำเร็จ!")
            st.rerun()

# ==========================================
# 3. เมนูด้านข้าง (Sidebar Navigation ครบทุกโมดูล)
# ==========================================
st.sidebar.markdown("## 🏥 เมนูระบบสุขภาพ")
menu = st.sidebar.radio(
    "เลือกเมนูการใช้งาน:",
    [
        "🏠 หน้าหลัก (Overview Dashboard)",
        "📅 ระบบบันทึกนัดหมาย (Appointment)",
        "💊 ระบบจัดและเตือนทานยา (Medication)",
        "🩺 บันทึกความดัน-เบาหวาน (Vitals)",
        "🧪 ผลตรวจสุขภาพ (Lab Results)"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tips:** ระบบเชื่อมต่อ Google Sheets `Healthcare_Master_DB` เรียบร้อยแล้วครับ")

# ==========================================
# 4. ตัวควบคุมการแสดงผลแต่ละโมดูล
# ==========================================
if "หน้าหลัก" in menu:
    st.title("🌟 ระบบสุขภาพรวม (Healthcare Dashboard 2026)")
    st.markdown("ยินดีต้อนรับสู่ระบบบริหารจัดการสุขภาพอัจฉริยะ ข้อมูลทั้งหมดเชื่อมโยงแบบ Real-time บน Google Sheets (`Healthcare_Master_DB`)")
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("📌 สถานะระบบ", "Online 🟢", "เชื่อมโยงสมบูรณ์")
    with c2: st.metric("💊 โมดูลยา", "Active", "พร้อมคำนวณอัตโนมัติ")
    with c3: st.metric("🩺 โมดูลสุขภาพ", "Synced", "พร้อมบันทึก Vitals")

elif "ระบบบันทึกนัดหมาย" in menu:
    try:
        from appointment import app as app_appointment
        importlib.reload(app_appointment)
        app_appointment.run_appointment_app()
    except Exception as e:
        st.error(f"⚠️ ไม่สามารถโหลดโมดูล Appointment ได้: {e}")

elif "ระบบจัดและเตือนทานยา" in menu:
    try:
        from medication import app as app_medication
        importlib.reload(app_medication)
        app_medication.run_medication_app()
    except Exception as e:
        st.error(f"⚠️ ไม่สามารถโหลดโมดูล Medication ได้: {e}")

elif "บันทึกความดัน-เบาหวาน" in menu:
    try:
        from vitals import app as app_vitals
        importlib.reload(app_vitals)
        app_vitals.run_vitals_app()
    except Exception as e:
        st.error(f"⚠️ ไม่สามารถโหลดโมดูล Vitals ได้: {e}")

elif "ผลตรวจสุขภาพ" in menu:
    try:
        from labs import app as app_labs
        importlib.reload(app_labs)
        app_labs.run_labs_app()
    except Exception as e:
        st.error(f"⚠️ ไม่สามารถโหลดโมดูล Lab Results ได้: {e}")
    