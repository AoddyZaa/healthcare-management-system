import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import io
import gspread
from google.oauth2.service_account import Credentials

def run_vitals_app():
    columns_order = ["วันที่", "เวลา / เหตุการณ์", "SYS", "DIA", "BPM", "FBS", "น้ำหนัก", "บันทึกเพิ่มเติม"]
    SPREADSHEET_NAME = "Healthcare_Master_DB"
    SHEET_NAME = "vitals"

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    def get_gcp_client():
        try:
            credentials = Credentials.from_service_account_file("appointment2026-3298e4cbba4f.json", scopes=SCOPES)
            return gspread.authorize(credentials)
        except Exception as e:
            st.error(f"❌ รายละเอียด Error เชื่อมต่อ Google Sheets: {e}")
            return None

    def format_thai_date(date_input):
        try:
            date_str = str(date_input).strip()
            if not date_str or date_str == "nan":
                return ""
            if 'T' in date_str:
                clean_date = date_str.split('T')[0].strip()
                dt = datetime.strptime(clean_date, "%Y-%m-%d")
            elif '-' in date_str:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                return date_str
            
            if dt.year > 2500:
                year_th = dt.year
            elif dt.year > 2200:
                year_th = 2026 + 543
            else:
                year_th = dt.year + 543
                
            day = dt.day
            month_names = ["", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
            month_str = month_names[dt.month]
            return f"{day} {month_str} {year_th}"
        except:
            return str(date_input)

    def convert_to_iso_date(date_str):
        try:
            date_str = str(date_str).strip()
            month_map = {"มกราคม": 1, "กุมภาพันธ์": 2, "มีนาคม": 3, "เมษายน": 4, "พฤษภาคม": 5, "มิถุนายน": 6, 
                         "กรกฎาคม": 7, "สิงหาคม": 8, "กันยายน": 9, "ตุลาคม": 10, "พฤศจิกายน": 11, "ธันวาคม": 12}
            parts = date_str.split()
            if len(parts) == 3 and parts[1] in month_map:
                day = int(parts[0])
                month = month_map[parts[1]]
                year = int(parts[2])
                if year > 2500:
                    year -= 543
                dt = datetime(year, month, day)
                return dt.strftime("%Y-%m-%d")
            return date_str
        except:
            return date_str

    def get_data():
        client = get_gcp_client()
        if not client:
            return pd.DataFrame(columns=columns_order)
        try:
            sh = client.open(SPREADSHEET_NAME)
            sheet = sh.worksheet(SHEET_NAME)
            all_values = sheet.get_all_values()
            if len(all_values) <= 1:
                return pd.DataFrame(columns=columns_order)
            
            records = []
            for row in all_values[1:]:
                padded = row + [""] * (len(columns_order) - len(row))
                row_data = {
                    "วันที่": format_thai_date(padded[0]),
                    "เวลา / เหตุการณ์": padded[1],
                    "SYS": padded[2],
                    "DIA": padded[3],
                    "BPM": padded[4],
                    "FBS": padded[5],
                    "น้ำหนัก": padded[6],
                    "บันทึกเพิ่มเติม": padded[7]
                }
                records.append(row_data)
                
            df = pd.DataFrame(records, columns=columns_order)
            return df[columns_order]
        except Exception as e:
            return pd.DataFrame(columns=columns_order)

    def save_data(df):
        client = get_gcp_client()
        if not client:
            st.error("ไม่สามารถเชื่อมต่อ Google Sheets ได้")
            return False
        try:
            df_to_save = df.copy()
            if 'วันที่' in df_to_save.columns:
                df_to_save['วันที่'] = df_to_save['วันที่'].apply(convert_to_iso_date)
            
            sh = client.open(SPREADSHEET_NAME)
            sheet = sh.worksheet(SHEET_NAME)
            sheet.clear()
            data_to_write = [columns_order] + df_to_save.astype(str).values.tolist()
            sheet.update(range_name='A1', values=data_to_write)
            return True
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการบันทึก: {e}")
            return False

    st.title("🩺 บันทึกสุขภาพเพื่อคุณหมอ 2026 💖")
    st.markdown("เชื่อมต่อ Google Sheets กลาง: **Healthcare_Master_DB** (Tab: `vitals`)")

    with st.expander("✨ บันทึกข้อมูลสุขภาพ (คลิกเพื่อเปิดฟอร์ม)", expanded=False):
        with st.form("health_form_modular", clear_on_submit=True):
            date_input = st.date_input("📅 วันที่วัด", datetime.now(), key="vitals_date_input")
            time_event = st.text_input("⏰ เวลา / เหตุการณ์ (เช่น เช้า, เย็น)", value="", placeholder="เช่น เช้า, เย็น", key="vitals_time_event")
            
            col1, col2 = st.columns(2)
            with col1:
                sys = st.number_input("❤️ ความดันตัวบน (SYS)", min_value=0, value=0, placeholder="ระบุค่า SYS", key="vitals_sys")
                dia = st.number_input("💙 ความดันตัวล่าง (DIA)", min_value=0, value=0, placeholder="ระบุค่า DIA", key="vitals_dia")
                bpm = st.number_input("💓 ชีพจร (BPM)", min_value=0, value=0, placeholder="ระบุชีพจร", key="vitals_bpm")
            with col2:
                fbs = st.number_input("🩸 น้ำตาลในเลือด (FBS)", min_value=0.0, value=0.0, placeholder="ระบุค่าน้ำตาล", key="vitals_fbs")
                weight = st.number_input("⚖️ น้ำหนัก (kg)", min_value=0.0, value=0.0, placeholder="ระบุน้ำหนัก", key="vitals_weight")
            
            note = st.text_input("📝 บันทึกเพิ่มเติม", value="", placeholder="ระบุหมายเหตุ (ถ้ามี)", key="vitals_note")
            
            if st.form_submit_button("🚀 บันทึกข้อมูลสุขภาพ", use_container_width=True):
                iso_date_str = date_input.strftime("%Y-%m-%d")
                new_row = {
                    "วันที่": iso_date_str,
                    "เวลา / เหตุการณ์": time_event,
                    "SYS": str(sys) if sys > 0 else "",
                    "DIA": str(dia) if dia > 0 else "",
                    "BPM": str(bpm) if bpm > 0 else "",
                    "FBS": str(fbs) if fbs > 0 else "",
                    "น้ำหนัก": str(weight) if weight > 0 else "",
                    "บันทึกเพิ่มเติม": note
                }
                df_current_raw = get_data()
                df_current_raw['วันที่'] = df_current_raw['วันที่'].apply(convert_to_iso_date)
                new_df = pd.DataFrame([new_row])
                final_df = pd.concat([df_current_raw, new_df], ignore_index=True)
                
                if save_data(final_df):
                    st.success("บันทึกข้อมูลสุขภาพเรียบร้อยครับ!")
                    st.rerun()

    df = get_data()

    st.subheader("📋 ตารางบันทึกข้อมูล (แก้ไข/ลบได้)")
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="health_editor_modular")

    if st.button("🔄 อัปเดตและบันทึกข้อมูลใหม่", key="vitals_update_btn"):
        if save_data(edited_df[columns_order]):
            st.success("อัปเดตข้อมูลออนไลน์เรียบร้อย!")
            st.rerun()

    # --- ส่วนระบบสำรองและกู้คืนข้อมูล (Backup & Restore) ---
    st.markdown("---")
    st.markdown("### 🛡️ ระบบสำรองและกู้คืนข้อมูล (Backup & Restore)")
    st.write("คุณสามารถดาวน์โหลดข้อมูลสุขภาพทั้งหมดเก็บไว้เป็นไฟล์ Excel หรืออัปโหลดไฟล์เพื่อกู้คืนข้อมูลกลับเข้า Google Sheets ได้ที่นี่ครับ")

    col_bk1, col_bk2 = st.columns(2)

    with col_bk1:
        st.markdown("### 1. ดาวน์โหลดข้อมูลเก็บไว้ในเครื่อง")
        df_backup = get_data()
        if not df_backup.empty:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_backup.to_excel(output, index=False, sheet_name='Sheet1')
            excel_data = output.getvalue()

            st.download_button(
                label="📥 ดาวน์โหลดไฟล์สำรองข้อมูล (.xlsx)",
                data=excel_data,
                file_name=f"health_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="vitals_download_btn"
            )
        else:
            st.info("ยังไม่มีข้อมูลสำหรับดาวน์โหลดสำรอง")

    with col_bk2:
        st.markdown("### 2. กู้คืนข้อมูลจากไฟล์ Excel")
        uploaded_file = st.file_uploader("📂 เลือกไฟล์สำรอง (.xlsx)", type=["xlsx"], key="restore_excel_vitals")
        if uploaded_file is not None:
            if st.button("🔄 ยืนยันการกู้คืนข้อมูลเข้า Google Sheets", use_container_width=True, key="vitals_restore_btn"):
                try:
                    restore_df = pd.read_excel(uploaded_file)
                    for col in columns_order:
                        if col not in restore_df.columns:
                            restore_df[col] = ""
                    restore_df = restore_df[columns_order]
                    if save_data(restore_df):
                        st.success("กู้คืนข้อมูลเข้า Google Sheets สำเร็จเรียบร้อยครับ!")
                        st.rerun()
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาดในการกู้คืนข้อมูล: {e}")