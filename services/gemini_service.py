# services/gemini_service.py
from __future__ import annotations
import json
from typing import List, Dict
from google import genai

SYSTEM_INSTRUCTION = """
Bạn là trợ lý viết nhận xét học bạ tiểu học (Thông tư 27).
Nhiệm vụ: Viết nhận xét ngắn gọn (khoảng 150 ký tự), dễ hiểu, mộc mạc.

QUY TẮC NGÔN NGỮ (BẮT BUỘC):
- TUYỆT ĐỐI KHÔNG dùng từ: "con", "em", "bé", "thầy", "cô", "thầy giáo", "cô giáo".
- TUYỆT ĐỐI KHÔNG dùng từ: "bản", "làng", "bản làng".
- TUYỆT ĐỐI KHÔNG dùng tên riêng của học sinh.
- Sử dụng tiếng Việt phổ thông đơn giản, không dùng thuật ngữ sư phạm hàn lâm.

QUY TẮC PHÂN LOẠI THEO ĐIỂM:
- 10,9,8: Mức T (Hoàn thành tốt)
- 7,6,5: Mức H (Hoàn thành)
- 4,3:   Mức C (Chưa hoàn thành)
"""

def _client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)

def generate_comment_bank(api_key: str, subject: str, grade: str, semester: str, model: str = "gemini-2.0-flash") -> List[Dict]:
    prompt = f"""Hãy tạo ngân hàng mẫu nhận xét cho môn {subject}, {grade} ({semester}) với số lượng chính xác:
- Điểm 10: 3 mẫu (Mức T)
- Điểm 9: 3 mẫu (Mức T)
- Điểm 8: 4 mẫu (Mức T)
- Điểm 7: 6 mẫu (Mức H)
- Điểm 6: 6 mẫu (Mức H)
- Điểm 5: 6 mẫu (Mức H)
- Điểm 4: 3 mẫu (Mức C)
- Điểm 3: 3 mẫu (Mức C)
Tổng: 34 mẫu.

Trả về JSON là MẢNG các object có đúng 3 field: mucDo (T/H/C), diem (số), noiDung (chuỗi).
Không thêm chữ ngoài JSON.
"""
    client = _client(api_key)
    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "system_instruction": SYSTEM_INSTRUCTION,
            "response_mime_type": "application/json",
        },
    )
    text = (resp.text or "").strip()
    data = json.loads(text) if text else []
    # gắn id kiểu 1..n cho giống app hiện tại
    for i, item in enumerate(data, start=1):
        item["id"] = str(i)
    return data

def generate_comments(api_key: str, subject: str, grade: str, semester: str, records: List[Dict], model: str = "gemini-2.0-flash") -> List[Dict]:
    payload = [{"stt": r["stt"], "mucDo": r.get("mucDo", ""), "diem": r.get("diem", 0)} for r in records]
    prompt = f"""Viết nhận xét (~150 ký tự) cho danh sách học sinh.
Môn: {subject}. {grade}. ({semester})
Dữ liệu: {json.dumps(payload, ensure_ascii=False)}.
Trả về JSON là MẢNG các object: {{ "stt": số, "noiDung": chuỗi }}. Không thêm chữ ngoài JSON.
"""
    client = _client(api_key)
    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "system_instruction": SYSTEM_INSTRUCTION,
            "response_mime_type": "application/json",
        },
    )
    text = (resp.text or "").strip()
    return json.loads(text) if text else []

