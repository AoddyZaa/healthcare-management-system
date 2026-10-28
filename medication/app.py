import datetime
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

def run_medication_app():
    # กำหนดค่าเชื่อมต่อ Google Sheets ไฟล์กลาง
    SPREADSHEET_NAME = "Healthcare_Master_DB"
    SHEET_NAME = "Medication_List"
    APPT_SHEET_NAME = "Appointment"

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    default_visit_date = "2026-10-27"
    default_appt_date = "2026-12-07"

    DEFAULT_MEDICATIONS = [
        {"แพทย์ผู้สั่งจ่าย": "หมอจุมพล", "ชื่อยา": "Less-K 5 g", "จำนวนต่อครั้ง": 1.0, "จำนวนครั้งต่อวัน": 2, "ยาคงเหลือเดิม": 0, "วันที่พบแพทย์ล่าสุด": default_visit_date, "วันที่นัดถัดไป": default_appt_date, "จำนวนที่ได้รับจริง": 0},
        {"แพทย์ผู้สั่งจ่าย": "หมอจุมพล", "ชื่อยา": "Furosemide 40 mg", "จำนวนต่อครั้ง": 2.0, "จำนวนครั้งต่อวัน": 1, "ยาคงเหลือเดิม": 0, "วันที่พบแพทย์ล่าสุด": default_visit_date, "วันที่นัดถัดไป": default_appt_date, "จำนวนที่ได้รับจริง": 0},
        {"แพทย์ผู้สั่งจ่าย": "หมอจุมพล", "ชื่อยา": "Sodamint 300 mg", "จำนวนต่อครั้ง": 1.0, "จำนวนครั้งต่อวัน": 3, "ยาคงเหลือเดิม": 0, "วันที่พบแพทย์ล่าสุด": default_visit_date, "วันที่นัดถัดไป": default_appt_date, "จำนวนที่ได้รับจริง": 0},
        {"แพทย์ผู้สั่งจ่าย": "หมอจุมพล", "ชื่อยา": "Amlodipine 5 mg", "จำนวนต่อครั้ง": 1.0, "จำนวนครั้งต่อวัน": 2, "ยาคงเหลือเดิม": 0, "วันที่พบแพทย์ล่าสุด": default_visit_date, "วันที่นัดถัดไป": default_appt_date, "จำนวนที่ได้รับจริง": 0},
        {"แพทย์ผู้สั่งจ่าย": "หมอจุมพล", "ชื่อยา": "Simvastatin 20 mg", "จำนวนต่อครั้ง": 0.5, "จำนวนครั้งต่อวัน": 1, "ยาคงเหลือเดิม": 0, "วันที่พบแพทย์ล่าสุด": default_visit_date, "วันที่นัดถัดไป": default_appt_date, "จำนวนที่ได้รับจริง": 0},
        {"แพทย์ผู้สั่งจ่าย": "หมอจุมพล", "ชื่อยา": "Doxazosin 2 mg", "จำนวนต่อครั้ง": 1.0, "จำนวนครั้งต่อวัน": 1, "ยาคงเหลือเดิม": 0, "วันที่พบแพทย์ล่าสุด": default_visit_date, "วันที่นัดถัดไป": default_appt_date, "จำนวนที่ได้รับจริง": 0},
        {"แพทย์ผู้สั่งจ่าย": "หมอจุมพล", "ชื่อยา": "Insulin 30/70", "จำนวนต่อครั้ง": 42.0, "จำนวนครั้งต่อวัน": 1, "ยาคงเหลือเดิม": 0, "วันที่พบแพทย์ล่าสุด": default_visit_date, "วันที่นัดถัดไป": default_appt_date, "จำนวนที่ได้รับจริง": 0},
        {"แพทย์ผู้สั่งจ่าย": "คุณหมอกิตติคุณ", "ชื่อยา": "Vit B. Complex", "จำนวนต่อครั้ง": 1.0, "จำนวนครั้งต่อวัน": 2, "ยาคงเหลือเดิม": 0, "วันที่พบแพทย์ล่าสุด": default_visit_date, "วันที่นัดถัดไป": default_appt_date, "จำนวนที่ได้รับจริง": 0},
    ]

    def get_gcp_client():
        try:
            credentials = Credentials.from_service_account_file("appointment2026-3298e4cbba4f.json", scopes=SCOPES)
            return gspread.authorize(credentials)
        except Exception as e:
            st.error(f"❌ รายละเอียด Error เชื่อมต่อ Google Sheets: {e}")
            return None

    def get_latest_appointment_date(doc_name):
        client = get_gcp_client()
        if not client:
            return None
        try:
            sh = client.open(SPREADSHEET_NAME)
            appt_sheet = sh.worksheet(APPT_SHEET_NAME)
            all_vals = appt_sheet.get_all_values()
            if len(all_vals) > 1:
                headers = [str(h).strip() for h in all_vals[0]]
                if "เจ้าของนัด" in headers and "วันที่นัด" in headers:
                    owner_idx = headers.index("เจ้าของนัด")
                    date_idx = headers.index("วันที่นัด")
                    dates = []
                    for row in all_vals[1:]:
                        if len(row) > max(owner_idx, date_idx):
                            row_owner = row[owner_idx].strip()
                            if doc_name.strip() in row_owner or row_owner in doc_name.strip():
                                dates.append(row[date_idx].strip())
                    if dates:
                        dates.sort(reverse=True)
                        return datetime.datetime.strptime(dates[0], "%Y-%m-%d").date()
        except Exception as e:
            print(e)
        return None

    def get_sheet_data():
        client = get_gcp_client()
        if not client:
            return None, DEFAULT_MEDICATIONS
        try:
            sh = client.open(SPREADSHEET_NAME)
            sheet = sh.worksheet(SHEET_NAME)
            all_values = sheet.get_all_values()
            records = []
            if len(all_values) > 1:
                headers = [str(h).strip() for h in all_values[0]]
                for row in all_values[1:]:
                    padded_row = row + [""] * (len(headers) - len(row))
                    row_dict = dict(zip(headers, [str(v).strip() for v in padded_row]))
                    
                    for num_col in ["จำนวนต่อครั้ง", "จำนวนครั้งต่อวัน", "ยาคงเหลือเดิม", "จำนวนที่ได้รับจริง"]:
                        if num_col in row_dict and row_dict[num_col] != "":
                            try:
                                row_dict[num_col] = float(row_dict[num_col]) if "." in row_dict[num_col] else int(row_dict[num_col])
                            except:
                                pass
                    records.append(row_dict)
                return sheet, records if records else DEFAULT_MEDICATIONS
            return sheet, DEFAULT_MEDICATIONS
        except Exception as e:
            st.error(f"⚠️ เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
            return None, DEFAULT_MEDICATIONS

    def save_to_sheet(df):
        client = get_gcp_client()
        if not client:
            return False
        try:
            sh = client.open(SPREADSHEET_NAME)
            sheet = sh.worksheet(SHEET_NAME)
            sheet.clear()
            data_to_write = [df.columns.tolist()] + df.astype(str).values.tolist()
            sheet.update(range_name='A1', values=data_to_write)
            return True
        except Exception as e:
            print(e)
            return False

    sheet, records = get_sheet_data()
    st.session_state["df_med"] = pd.DataFrame(records if records else DEFAULT_MEDICATIONS)
    df_all = st.session_state["df_med"]

    st.title("💊 ระบบติดตามการจัดยาและวันนัดแพทย์ 2026 ❤️")
    st.markdown("เชื่อมต่อ Google Sheets กลาง: **Healthcare_Master_DB** (Tab: `Medication_List`)")
    st.markdown("---")

    existing_doctors = df_all["แพทย์ผู้สั่งจ่าย"].dropna().unique().tolist() if not df_all.empty else ["หมอจุมพล", "คุณหมอกิตติคุณ"]
    
    with st.expander("🩺 เลือกแพทย์ & จัดการยา (คลิกเพื่อเปิดเมนูตั้งค่า)", expanded=False):
        doctor_options = existing_doctors + ["➕ เพิ่มแพทย์ใหม่..."]
        selected_doc_option = st.selectbox("เลือกแพทย์ผู้สั่งจ่าย:", doctor_options, key="med_doc_opt_master")
        
        doc_name = st.text_input("ระบุชื่อแพทย์ท่านใหม่:", value="", key="med_new_doc_master") if selected_doc_option == "➕ เพิ่มแพทย์ใหม่..." else selected_doc_option

        latest_appt = get_latest_appointment_date(doc_name)
        default_appt_val = latest_appt if latest_appt else datetime.date(2026, 12, 7)

        st.markdown("---")
        st.subheader("📅 บันทึกวันนัดหมาย & คำนวณยา")
        visit_date = st.date_input("วันที่พบแพทย์ล่าสุด", value=datetime.date(2026, 10, 27), key="med_visit_date_master")
        next_appt_date = st.date_input("วันที่แพทย์นัดครั้งต่อไป (ดึงจากนัดหมายล่าสุด)", value=default_appt_val, key="med_appt_date_master")

        if st.button("💾 บันทึก & อัปเดตวันนัดและจำนวนยา (แพทย์ท่านนี้)", use_container_width=True, type="primary", key="med_update_doc_btn_master"):
            days = max(0, (next_appt_date - visit_date).days)
            def calc_rec(row):
                if row["แพทย์ผู้สั่งจ่าย"] == doc_name:
                    try:
                        return max(0.0, round((float(row["จำนวนต่อครั้ง"]) * int(row["จำนวนครั้งต่อวัน"]) * days) - float(row["ยาคงเหลือเดิม"]), 1))
                    except:
                        return row["จำนวนที่ได้รับจริง"]
                return row["จำนวนที่ได้รับจริง"]

            st.session_state["df_med"].loc[st.session_state["df_med"]["แพทย์ผู้สั่งจ่าย"] == doc_name, "วันที่พบแพทย์ล่าสุด"] = visit_date.strftime("%Y-%m-%d")
            st.session_state["df_med"].loc[st.session_state["df_med"]["แพทย์ผู้สั่งจ่าย"] == doc_name, "วันที่นัดถัดไป"] = next_appt_date.strftime("%Y-%m-%d")
            st.session_state["df_med"]["จำนวนที่ได้รับจริง"] = st.session_state["df_med"].apply(calc_rec, axis=1)
            save_to_sheet(st.session_state["df_med"])
            st.success("🎉 อัปเดตข้อมูลเฉพาะแพทย์ท่านนี้เรียบร้อยและซิงค์ขึ้น Google Sheets แล้ว!")
            st.rerun()

        st.markdown("---")
        st.subheader("💊 เพิ่มยาใหม่ในสังกัดแพทย์นี้")
        with st.form("add_med_form_master", clear_on_submit=True):
            med_name = st.text_input("ชื่อยาใหม่", value="", placeholder="ระบุชื่อยา", key="med_name_input_new")
            dose_val = st.number_input("จำนวนต่อครั้ง", min_value=0.1, value=1.0, step=0.5, key="med_dose_input_new")
            times_val = st.number_input("จำนวนครั้งต่อวัน", min_value=1, value=1, step=1, key="med_times_input_new")
            remain_val = st.number_input("ยาคงเหลือเดิม", min_value=0.0, value=0.0, step=0.5, key="med_remain_input_new")
            
            if st.form_submit_button("➕ เพิ่มยาเข้าระบบ", use_container_width=True):
                if med_name.strip():
                    new_item = {
                        "แพทย์ผู้สั่งจ่าย": doc_name.strip(),
                        "ชื่อยา": med_name.strip(),
                        "จำนวนต่อครั้ง": dose_val,
                        "จำนวนครั้งต่อวัน": times_val,
                        "ยาคงเหลือเดิม": remain_val,
                        "วันที่พบแพทย์ล่าสุด": visit_date.strftime("%Y-%m-%d"),
                        "วันที่นัดถัดไป": next_appt_date.strftime("%Y-%m-%d"),
                        "จำนวนที่ได้รับจริง": 0.0
                    }
                    st.session_state["df_med"] = pd.concat([st.session_state["df_med"], pd.DataFrame([new_item])], ignore_index=True)
                    save_to_sheet(st.session_state["df_med"])
                    st.success("🎉 เพิ่มรายการยาสำเร็จ!")
                    st.rerun()

    filter_doc = st.selectbox("🔍 กรองแสดงรายการยาตามแพทย์:", ["แสดงทั้งหมด"] + existing_doctors, key="med_filter_doc_master")
    editor_df = st.session_state["df_med"].copy()
    if filter_doc != "แสดงทั้งหมด":
        editor_df = editor_df[editor_df["แพทย์ผู้สั่งจ่าย"] == filter_doc]

    edited_df = st.data_editor(editor_df, num_rows="dynamic", use_container_width=True, key="main_med_editor_master")

    if st.button("💾 บันทึกการแก้ไขข้อมูลทั้งหมด", use_container_width=True, key="med_save_edit_btn_master"):
        st.session_state["df_med"] = edited_df
        save_to_sheet(st.session_state["df_med"])
        st.success("🎉 บันทึกข้อมูลสำเร็จ!")
        st.rerun()