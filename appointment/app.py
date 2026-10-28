import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime

def run_appointment_app():
    # กำหนดค่าเชื่อมต่อ Google Sheets ไฟล์กลาง
    SPREADSHEET_NAME = "Healthcare_Master_DB"
    SHEET_NAME = "Appointment"
    MED_SHEET_NAME = "Medication_List"

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    def get_gcp_client():
        try:
            # ดึงข้อมูลจาก st.secrets โดยตรง เพื่อรองรับ Streamlit Cloud (ปลอดภัย ไม่ต้องใช้ไฟล์ JSON บนคลาวด์)
            if "gcp_service_account" in st.secrets:
                secrets_dict = dict(st.secrets["gcp_service_account"])
                credentials = Credentials.from_service_account_info(secrets_dict, scopes=SCOPES)
                return gspread.authorize(credentials)
            else:
                st.error("❌ ไม่พบข้อมูล gcp_service_account ใน Streamlit Secrets")
                return None
        except Exception as e:
            st.error(f"❌ Error: {e}")
            return None

    def load_data():
        client = get_gcp_client()
        columns_order = ["วันที่นัด", "เวลานัด", "รายการนัด", "นัดโดย", "เจ้าของนัด", "สถานที่", "เบอร์โทร", "หมายเหตุ"]
        
        if not client:
            st.error("⚠️ ไม่สามารถเชื่อมต่อ Google Sheets ได้")
            return pd.DataFrame(columns=columns_order)
        
        try:
            sh = client.open(SPREADSHEET_NAME)
            sheet = sh.worksheet(SHEET_NAME)
            all_values = sheet.get_all_values()
            
            if len(all_values) > 1:
                headers = [str(h).strip() for h in all_values[0]]
                records = []
                for row in all_values[1:]:
                    padded = row + [""] * (len(headers) - len(row))
                    records.append(dict(zip(headers, [str(v).strip() for v in padded])))
                df = pd.DataFrame(records)
                
                for col in columns_order:
                    if col not in df.columns:
                        df[col] = ""
                return df[columns_order]
            else:
                return pd.DataFrame(columns=columns_order)
        except Exception as e:
            st.error(f"⚠️ เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
            return pd.DataFrame(columns=columns_order)

    def get_existing_doctors():
        """ดึงรายชื่อแพทย์ทั้งหมดที่มีอยู่ในระบบจัดการยาและนัดหมายมาทำ Dropdown"""
        doctors = set()
        client = get_gcp_client()
        if not client:
            return ["-- เพิ่มแพทย์/เจ้าของนัดใหม่ --"]
        try:
            sh = client.open(SPREADSHEET_NAME)
            
            # ดึงจากแท็บ Medication_List
            try:
                med_sheet = sh.worksheet(MED_SHEET_NAME)
                med_vals = med_sheet.get_all_values()
                if len(med_vals) > 1:
                    headers = [str(h).strip() for h in med_vals[0]]
                    if "แพทย์ผู้สั่งจ่าย" in headers:
                        idx = headers.index("แพทย์ผู้สั่งจ่าย")
                        for row in med_vals[1:]:
                            if len(row) > idx and row[idx].strip():
                                doctors.add(row[idx].strip())
            except:
                pass

            # ดึงจากแท็บ Appointment เดิมด้วย
            try:
                appt_sheet = sh.worksheet(SHEET_NAME)
                appt_vals = appt_sheet.get_all_values()
                if len(appt_vals) > 1:
                    headers = [str(h).strip() for h in appt_vals[0]]
                    if "เจ้าของนัด" in headers:
                        idx = headers.index("เจ้าของนัด")
                        for row in appt_vals[1:]:
                            if len(row) > idx and row[idx].strip():
                                doctors.add(row[idx].strip())
            except:
                pass
                
        except Exception as e:
            print(e)
            
        doc_list = sorted(list(doctors))
        return doc_list + ["➕ เพิ่มแพทย์/เจ้าของนัดใหม่..."]

    def save_data(df):
        client = get_gcp_client()
        if not client:
            return False
        try:
            sh = client.open(SPREADSHEET_NAME)
            sheet = sh.worksheet(SHEET_NAME)
            sheet.clear()
            data_to_write = [df.columns.tolist()] + df.astype(str).values.tolist()
            sheet.update('A1', data_to_write)
            return True
        except Exception as e:
            print(e)
            return False

    def sync_medication_appointment(doc_name, new_appt_date):
        """ฟังก์ชันซิงค์วันนัดและคำนวณจำนวนยาอัจฉริยะ (Exact & Fuzzy Match)"""
        client = get_gcp_client()
        if not client:
            return
        try:
            sh = client.open(SPREADSHEET_NAME)
            med_sheet = sh.worksheet(MED_SHEET_NAME)
            all_vals = med_sheet.get_all_values()
            if len(all_vals) <= 1:
                return
            
            headers = [str(h).strip() for h in all_vals[0]]
            med_records = []
            for row in all_vals[1:]:
                padded = row + [""] * (len(headers) - len(row))
                med_records.append(dict(zip(headers, [str(v).strip() for v in padded])))
            
            med_df = pd.DataFrame(med_records)
            found_doctor = False
            
            doc_clean = doc_name.strip()
            
            if "แพทย์ผู้สั่งจ่าย" in med_df.columns:
                for idx, row in med_df.iterrows():
                    row_doc = str(row["แพทย์ผู้สั่งจ่าย"]).strip()
                    # เช็คชื่อแพทย์แบบตรงกันเป๊ะ หรือมีคำค้นตรงกันเพื่อความแม่นยำสูงสุด
                    if doc_clean == row_doc or doc_clean in row_doc or row_doc in doc_clean:
                        found_doctor = True
                        visit_date_str = row.get("วันที่พบแพทย์ล่าสุด", datetime.date.today().strftime("%Y-%m-%d"))
                        try:
                            v_date = datetime.datetime.strptime(visit_date_str, "%Y-%m-%d").date()
                            days = max(0, (new_appt_date - v_date).days)
                            dose = float(row.get("จำนวนต่อครั้ง", 1) or 1)
                            times = int(float(row.get("จำนวนครั้งต่อวัน", 1) or 1))
                            remain = float(row.get("ยาคงเหลือเดิม", 0) or 0)
                            
                            # คำนวณจำนวนยาที่ได้รับจริงตามวันนัดใหม่ที่ห่างจากวันพบแพทย์ล่าสุด
                            calculated_qty = max(0.0, round((dose * times * days) - remain, 1))
                            med_df.loc[idx, "วันที่นัดถัดไป"] = new_appt_date.strftime("%Y-%m-%d")
                            med_df.loc[idx, "จำนวนที่ได้รับจริง"] = calculated_qty
                        except Exception as ex:
                            print(ex)
            
            # ถ้าเป็นแพทย์ท่านใหม่ ให้เพิ่มแถวตั้งต้นใน Medication_List ทันที
            if not found_doctor:
                new_med_row = {
                    "แพทย์ผู้สั่งจ่าย": doc_name,
                    "ชื่อยา": "ยาตามแพทย์สั่ง (ระบุชื่อยาเพิ่ม)",
                    "จำนวนต่อครั้ง": "1.0",
                    "จำนวนครั้งต่อวัน": "1",
                    "ยาคงเหลือเดิม": "0",
                    "วันที่พบแพทย์ล่าสุด": datetime.date.today().strftime("%Y-%m-%d"),
                    "วันที่นัดถัดไป": new_appt_date.strftime("%Y-%m-%d"),
                    "จำนวนที่ได้รับจริง": "30.0"
                }
                med_df = pd.concat([med_df, pd.DataFrame([new_med_row])], ignore_index=True)

            med_sheet.clear()
            med_data_to_write = [med_df.columns.tolist()] + med_df.astype(str).values.tolist()
            med_sheet.update('A1', med_data_to_write)
        except Exception as e:
            print(f"Sync error: {e}")

    st.title("📅 ระบบบันทึกและจัดการนัดหมาย")
    st.markdown("เชื่อมต่อ Google Sheets กลาง: **Healthcare_Master_DB** (Tab: `Appointment` & `Medication_List`)")

    df = load_data()
    doctor_options = get_existing_doctors()

    with st.expander("📌 เพิ่มนัดหมายใหม่ (คลิกเพื่อเปิดฟอร์ม)", expanded=True):
        with st.form("add_appointment_form_master", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                appt_date = st.date_input("วันที่นัดหมาย", value=datetime.date.today(), key="appt_date_new")
                appt_time = st.time_input("เวลานัดหมาย", value=datetime.time(9, 0), key="appt_time_new")
                appt_title = st.text_input("รายการนัด (เช่น พบแพทย์, เจาะเลือด)", placeholder="ระบุรายการนัด", key="appt_title_new")
                appt_by = st.selectbox("นัดโดย", ["โรงพยาบาล", "ญาติ/ผู้ดูแล", "ตนเอง"], key="appt_by_new")
            with c2:
                selected_doc = st.selectbox("เลือกเจ้าของนัด (แพทย์/ผู้ป่วย)", doctor_options, key="appt_doc_select")
                
                custom_doc = ""
                if "➕ เพิ่มแพทย์" in selected_doc:
                    custom_doc = st.text_input("ระบุชื่อแพทย์/เจ้าของนัดใหม่", placeholder="พิมพ์ชื่อ-นามสกุลแพทย์", key="appt_custom_doc")
                
                appt_location = st.text_input("สถานที่นัด", placeholder="ระบุสถานที่", key="appt_loc_new")
                appt_phone = st.text_input("เบอร์โทรติดต่อ", placeholder="ระบุเบอร์โทร", key="appt_phone_new")
                appt_note = st.text_area("หมายเหตุเพิ่มเติม", placeholder="ระบุหมายเหตุ (ถ้ามี)", key="appt_note_new")

            if st.form_submit_button("💾 บันทึกนัดหมายใหม่", type="primary", use_container_width=True):
                final_owner = custom_doc.strip() if custom_doc else selected_doc
                if "➕" in final_owner or not final_owner:
                    st.warning("⚠️ กรุณาระบุหรือเลือกชื่อเจ้าของนัด (ชื่อแพทย์/ผู้ป่วย) ให้ถูกต้อง")
                else:
                    new_row = {
                        "วันที่นัด": appt_date.strftime("%Y-%m-%d"),
                        "เวลานัด": appt_time.strftime("%H:%M"),
                        "รายการนัด": appt_title,
                        "นัดโดย": appt_by,
                        "เจ้าของนัด": final_owner,
                        "สถานที่": appt_location,
                        "เบอร์โทร": appt_phone,
                        "หมายเหตุ": appt_note
                    }
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    if "วันที่นัด" in df.columns:
                        df = df.sort_values(by=["วันที่นัด", "เวลานัด"]).reset_index(drop=True)
                    
                    if save_data(df):
                        sync_medication_appointment(final_owner, appt_date)
                        st.success("🎉 บันทึกนัดหมายสำเร็จ และซิงค์อัปเดตวันนัดพร้อมคำนวณจำนวนยาลง Google Sheets เรียบร้อยแล้ว!")
                        st.rerun()
                    else:
                        st.warning("⚠️ บันทึกไม่สำเร็จ โปรดตรวจสอบการเชื่อมต่อ Google Sheets")

    st.markdown("---")
    st.subheader("📋 รายการนัดหมายทั้งหมด")
    
    if not df.empty:
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="appt_editor_master")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("💾 บันทึกการแก้ไขตารางนัดหมาย", use_container_width=True, type="primary", key="save_appt_edit"):
                if save_data(edited_df):
                    st.success("🎉 บันทึกการเปลี่ยนแปลงสำเร็จ!")
                    st.rerun()
                else:
                    st.error("เกิดข้อผิดพลาดในการบันทึกข้อมูล")
        with col_btn2:
            if st.button("🔄 รีเฟรชข้อมูลล่าสุด", use_container_width=True, key="refresh_appt"):
                st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลนัดหมายในระบบ")