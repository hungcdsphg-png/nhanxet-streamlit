# app.py
from __future__ import annotations
import streamlit as st
import pandas as pd

from utils.rules import KHOI_LOP, MON_HOC_TIEU_HOC, BankComment, generate_code_and_autofill
from utils.excel_io import read_students_from_excel, export_students_excel, export_bank_excel
from services.gemini_service import generate_comment_bank, generate_comments

st.set_page_config(page_title="Trợ Lý Tạo Nhận Xét", layout="wide")

st.title("Trợ Lý Tạo Nhận Xét")
st.caption("Nhập Excel → tạo ngân hàng 34 mẫu → tự gợi ý nhận xét theo điểm/mức → xuất Excel.")

# --- secrets ---
api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    st.warning("Chưa có GEMINI_API_KEY trong Secrets. Vào Settings → Secrets để thêm.")

# --- session state ---
if "bank" not in st.session_state:
    st.session_state.bank = []      # list[dict]
if "records" not in st.session_state:
    st.session_state.records = []   # list[dict]

# --- sidebar controls ---
with st.sidebar:
    grade = st.selectbox("Khối", KHOI_LOP, index=1)
    subject = st.selectbox("Môn", MON_HOC_TIEU_HOC, index=0)
    semester = st.selectbox("Học kỳ", ["Học kỳ 1", "Học kỳ 2"], index=0)
    model = st.text_input("Model (tuỳ chọn)", value="gemini-2.0-flash")

colA, colB, colC = st.columns([1, 1, 2])

with colA:
    if st.button("✨ Tạo 34 mẫu nhận xét", use_container_width=True, disabled=(not api_key)):
        with st.spinner("Đang tạo ngân hàng 34 mẫu..."):
            bank = generate_comment_bank(api_key, subject, grade, semester, model=model)
            st.session_state.bank = bank
        st.success(f"Đã tạo {len(st.session_state.bank)} mẫu.")

with colB:
    uploaded = st.file_uploader("📥 Nhập Excel (.xlsx)", type=["xlsx"])

    if uploaded is not None:
        try:
            st.session_state.records = read_students_from_excel(uploaded.getvalue(), subject)
            st.success(f"Đã nhập {len(st.session_state.records)} học sinh từ Excel.")
        except Exception as e:
            st.error(str(e))

with colC:
    st.write("**Quy tắc mức theo điểm (đang bám logic app của bạn):**")
    st.write("- 10, 9, 8 → T; 7, 6, 5 → H; 4, 3 → C (điểm 0 thì mặc định H).")
    st.write("- Mã NX: `[Môn][Điểm][Mức][STT]` và tự gợi ý nội dung từ ngân hàng theo nhóm điểm/mức.")

# --- process ---
bank_comments = []
for b in st.session_state.bank:
    try:
        bank_comments.append(BankComment(mucDo=b["mucDo"], diem=int(b["diem"]), noiDung=b["noiDung"]))
    except Exception:
        pass

if st.session_state.records:
    processed = generate_code_and_autofill(st.session_state.records, bank_comments, subject)

    st.subheader("Bảng học sinh (có thể sửa nội dung trực tiếp)")
    df = pd.DataFrame(processed)

    # cho sửa noiDung ngay trên bảng
    edited = st.data_editor(
        df[["stt", "hoTen", "mucDo", "diem", "maNhanXet", "noiDung"]],
        use_container_width=True,
        num_rows="fixed",
        hide_index=True,
    )

    # cập nhật lại session records từ bản edited
    st.session_state.records = edited.to_dict("records")

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        if st.button("🤖 Gemini viết nhận xét theo danh sách", disabled=(not api_key)):
            with st.spinner("Đang gọi Gemini..."):
                res = generate_comments(api_key, subject, grade, semester, st.session_state.records, model=model)
            # map theo stt
            m = {int(x["stt"]): x["noiDung"] for x in res if "stt" in x and "noiDung" in x}
            st.session_state.records = [
                {**r, "noiDung": m.get(int(r["stt"]), r.get("noiDung", ""))}
                for r in st.session_state.records
            ]
            st.success("Đã cập nhật nhận xét từ Gemini.")

    with c2:
        out_bytes = export_students_excel(st.session_state.records)
        st.download_button(
            "⬇️ Xuất nhận xét (Excel)",
            data=out_bytes,
            file_name=f"NhanXet_{grade}_{subject}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with c3:
        if st.session_state.bank:
            # format ngân hàng giống bảng export của bạn
            bank_export = []
            for i, b in enumerate(st.session_state.bank, start=1):
                bank_export.append({
                    "STT": i,
                    "Mã nhận xét": b.get("id", str(i)),
                    "Mức đạt": b.get("mucDo", ""),
                    "Điểm số": b.get("diem", ""),
                    "Nội dung nhận xét phổ thông": b.get("noiDung", ""),
                })
            bank_bytes = export_bank_excel(bank_export)
            st.download_button(
                "⬇️ Xuất ngân hàng 34 mẫu (Excel)",
                data=bank_bytes,
                file_name=f"NganHang_{grade}_{subject}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

st.divider()
st.caption("Gợi ý: nếu bạn muốn UI giống bản React hiện tại hơn, mình có thể thêm tab 'Học sinh' / 'Ngân hàng 34 mẫu' và ô tìm kiếm.")

