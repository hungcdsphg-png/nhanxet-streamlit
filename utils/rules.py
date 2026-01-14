# utils/rules.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple

KHOI_LOP = ["Khối 1", "Khối 2", "Khối 3", "Khối 4", "Khối 5"]

MON_HOC_TIEU_HOC = [
    "Tiếng Việt", "Toán", "Tiếng Anh", "Đạo đức", "Tự nhiên và Xã hội",
    "Lịch sử và Địa lý", "Khoa học", "Tin học", "Công nghệ",
    "Giáo dục thể chất", "Nghệ thuật (Âm nhạc)", "Nghệ thuật (Mỹ thuật)",
    "Hoạt động trải nghiệm"
]

SUBJECT_ABBR = {
    "Tiếng Việt": "TV",
    "Toán": "T",
    "Tiếng Anh": "TA",
    "Đạo đức": "DD",
    "Tự nhiên và Xã hội": "TNXH",
    "Lịch sử và Địa lý": "LSDL",
    "Khoa học": "KH",
    "Tin học": "TH",
    "Công nghệ": "CN",
    "Giáo dục thể chất": "GDTC",
    "Nghệ thuật (Âm nhạc)": "AN",
    "Nghệ thuật (Mỹ thuật)": "MT",
    "Hoạt động trải nghiệm": "HDTN",
}

def get_subject_abbr(subject: str) -> str:
    return SUBJECT_ABBR.get(subject, "MH")

def level_from_score(score: float) -> str:
    s = int(round(score)) if score and score > 0 else 0
    if s >= 8:
        return "T"
    if s >= 5:
        return "H"
    if s >= 1:
        return "C"
    return "H"

@dataclass
class BankComment:
    mucDo: str   # 'T'|'H'|'C'
    diem: int
    noiDung: str

def generate_code_and_autofill(records: List[dict], bank: List[BankComment], subject: str) -> List[dict]:
    abbr = get_subject_abbr(subject)
    counters: Dict[str, int] = {}

    # nhóm bank theo điểm và theo mức
    by_score: Dict[int, List[BankComment]] = {}
    by_level: Dict[str, List[BankComment]] = {"T": [], "H": [], "C": []}
    for b in bank:
        by_score.setdefault(int(b.diem), []).append(b)
        by_level.setdefault(b.mucDo, []).append(b)

    out = []
    for r in records:
        score = int(round(r.get("diem", 0) or 0))
        level = level_from_score(score)
        key = f"{score}_{level}"
        counters[key] = counters.get(key, 0) + 1

        score_str = str(score) if score > 0 else ""
        code = r.get("maNhanXet") or f"{abbr}{score_str}{level}{counters[key]}"

        # chọn nhóm nhận xét
        if score > 0 and score in by_score and by_score[score]:
            group = by_score[score]
        else:
            group = by_level.get(level, [])

        noi_dung = r.get("noiDung") or ""
        if (not noi_dung) and group:
            idx = (counters[key] - 1) % len(group)
            noi_dung = group[idx].noiDung

        out.append({**r, "mucDo": level, "maNhanXet": code, "noiDung": noi_dung})
    return out

