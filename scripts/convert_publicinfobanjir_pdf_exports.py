"""OCR user-saved Public InfoBanjir PDF pages into provenance-labelled CSVs."""
from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pypdfium2 as pdfium
from rapidocr_onnxruntime import RapidOCR

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = Path.home() / "Downloads"
OUT_DIR = ROOT / "data" / "processed" / "user_provided_csv"
BASE = "https://publicinfobanjir.water.gov.my"
FILES = {
    "rainfallkl.pdf": ("rainfall", "Kuala Lumpur", "WLH", "hujan/data-hujan/?state=WLH&lang=en"),
    "rainfallputrajaya.pdf": ("rainfall", "Putrajaya", "PTJ", "hujan/data-hujan/?state=PTJ&lang=en"),
    "rainfallselangor.pdf": ("rainfall", "Selangor", "SEL", "hujan/data-hujan/?state=SEL&lang=en"),
    "waterlevelkl.pdf": ("waterlevel", "Kuala Lumpur", "WLH", "aras-air/data-paras-air/aras-air-data/?state=WLH&lang=en"),
    "waterlevelputrajaya.pdf": ("waterlevel", "Putrajaya", "PTJ", "aras-air/data-paras-air/aras-air-data/?state=PTJ&lang=en"),
    "waterlevelselangor.pdf": ("waterlevel", "Selangor", "SEL", "aras-air/data-paras-air/aras-air-data/?state=SEL&lang=en"),
}
RAIN_X = [0, .07, .14, .23, .32, .405, .485, .545, .61, .675, .74, .81, .90, .925, 1.01]
WATER_X = [0, .08, .15, .26, .35, .42, .50, .61, .75, .81, .855, .91, .96, 1.01]
RAIN_SEL_X = [0, .07, .14, .20, .27, .323, .385, .449, .514, .578, .64, .74, .88, .90, 1.01]
WATER_SEL_X = [0, .08, .15, .26, .33, .395, .46, .56, .72, .81, .855, .90, .96, 1.01]
DATE_RE = re.compile(r"\d{1,2}/\d{1,2}/\d{4}")
NUM_RE = re.compile(r"(?<!\d)-?\d+(?:\.\d+)?")


def ocr_page(engine, path: Path, page_no: int):
    doc = pdfium.PdfDocument(path)
    image = doc[page_no].render(scale=1.5).to_numpy()
    detections, _ = engine(image)
    width = image.shape[1]
    tokens = []
    for box, text, score in detections or []:
        tokens.append({"x": sum(p[0] for p in box) / 4 / width,
                       "y": sum(p[1] for p in box) / 4,
                       "text": text, "score": float(score)})
    return tokens


def group_rows(tokens, kind, state):
    id_re = re.compile(r"^\d{5,10}(?:RF|WL)?$", re.I)
    anchors = [t for t in tokens if id_re.fullmatch(t["text"].strip()) and .06 <= t["x"] <= .16 and t["y"] > 100]
    # Distinct station identifiers anchor rows; order from top to bottom.
    anchors.sort(key=lambda t: t["y"])
    if not anchors:
        return []
    groups = [[] for _ in anchors]
    for i, anchor in enumerate(anchors):
        lower = (anchors[i - 1]["y"] + anchor["y"]) / 2 if i else anchor["y"] - (anchors[1]["y"] - anchor["y"]) / 2 if len(anchors) > 1 else anchor["y"] - 25
        upper = (anchor["y"] + anchors[i + 1]["y"]) / 2 if i + 1 < len(anchors) else anchor["y"] + (anchor["y"] - anchors[i - 1]["y"]) / 2 if i else anchor["y"] + 25
        groups[i] = [t for t in tokens if lower <= t["y"] < upper]
    bounds = (RAIN_SEL_X if state == "Selangor" else RAIN_X) if kind == "rainfall" else (WATER_SEL_X if state == "Selangor" else WATER_X)
    rows = []
    for group, anchor in zip(groups, anchors):
        fields = [[] for _ in range(len(bounds) - 1)]
        for t in group:
            col = next((i for i in range(len(bounds)-1) if bounds[i] <= t["x"] < bounds[i+1]), None)
            if col is not None:
                fields[col].append(t)
        # Preserve top-to-bottom ordering for wrapped names and dates.
        for f in fields:
            f.sort(key=lambda t: (t["y"], t["x"]))
        rows.append(fields)
    return rows


def text(fields, col):
    return " ".join(t["text"] for t in fields[col]).strip()


def first_num(s):
    m = NUM_RE.search(s.replace(",", ""))
    return m.group(0) if m else ""


def parse_page(tokens, kind, state):
    result = []
    for fields in group_rows(tokens, kind, state):
        if kind == "rainfall":
            date_fields = [text(fields, i) for i in range(5, 11)]
            # The site table has six fixed daily columns, confirmed from its PDF header.
            dates = [f"{day:02d}/11/2026" for day in range(6, 12)]
            row = {
                "station_id": text(fields, 1), "station_name": text(fields, 2),
                "district": text(fields, 3), "last_updated": text(fields, 4),
                **{f"daily_{datetime.strptime(d,'%d/%m/%Y').strftime('%Y_%m_%d')}_mm": first_num(DATE_RE.sub("", date_fields[i]))
                   for i, d in enumerate(dates)},
                "rainfall_from_midnight_mm": first_num(text(fields, 11)),
                "total_1_hour_mm": first_num(text(fields, 13)),
            }
        else:
            # Date and time are often separate OCR detections in the same cell.
            updated_raw = text(fields, 6)
            date_match = DATE_RE.search(updated_raw)
            time_match = re.search(r"\d{1,2}:\d{2}(?::\d{2})?", updated_raw)
            updated = (date_match.group(0) + (" " + time_match.group(0) if time_match else "")) if date_match else updated_raw
            row = {
                "station_id": text(fields, 1), "station_name": text(fields, 2),
                "district": text(fields, 3), "main_basin": text(fields, 4),
                "sub_river_basin": text(fields, 5), "last_updated": updated,
                "water_level_m": first_num(text(fields, 7)),
                "threshold_normal_m": first_num(text(fields, 8)),
                "threshold_alert_m": first_num(text(fields, 9)),
                "threshold_warning_m": first_num(text(fields, 10)),
                "threshold_danger_m": first_num(text(fields, 11)),
            }
        result.append(row)
    return result


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    engine = RapidOCR()
    all_by_kind = {"rainfall": [], "waterlevel": []}
    for filename, (kind, state, state_code, path) in FILES.items():
        pdf_path = PDF_DIR / filename
        doc = pdfium.PdfDocument(pdf_path)
        captured = datetime.fromtimestamp(pdf_path.stat().st_mtime, ZoneInfo("Asia/Kuala_Lumpur")).isoformat(timespec="seconds")
        rows = []
        for page_no in range(len(doc)):
            page_rows = parse_page(ocr_page(engine, pdf_path, page_no), kind, state)
            for row in page_rows:
                row.update({
                    "state": state, "source": "Public InfoBanjir",
                    "source_method": "OCR transcription from user-provided saved website PDF; not a live API import",
                    "source_url": f"{BASE}/{path}", "source_document": filename,
                    "source_page": page_no + 1, "captured_at_local": captured,
                    "ocr_review_status": "needs_visual_review",
                })
                rows.append(row)
        # Flatten to consistent headers per table; retain rows even when OCR missed a value.
        core = (list(rows[0].keys()) if rows else [])
        if not core:
            core = ((["station_id", "station_name", "district", "last_updated", "rainfall_from_midnight_mm", "total_1_hour_mm"] if kind == "rainfall" else
                     ["station_id", "station_name", "district", "main_basin", "sub_river_basin", "last_updated", "water_level_m", "threshold_normal_m", "threshold_alert_m", "threshold_warning_m", "threshold_danger_m"]) +
                    ["state", "source", "source_method", "source_url", "source_document", "source_page", "captured_at_local", "ocr_review_status"])
        # Put provenance first for easy downstream filtering.
        provenance = ["source", "source_method", "source_document", "source_page", "source_url", "captured_at_local", "ocr_review_status", "state"]
        headers = provenance + [key for key in core if key not in provenance]
        out = OUT_DIR / filename.replace(".pdf", ".csv")
        with out.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
            writer.writeheader(); writer.writerows(rows)
        all_by_kind[kind].extend(rows)
        print(f"{filename}: {len(rows)} station rows -> {out.relative_to(ROOT)}")
    for kind, rows in all_by_kind.items():
        # Union daily rainfall date columns across state files.
        fields = []
        for row in rows:
            for key in row:
                if key not in fields: fields.append(key)
        provenance = ["source", "source_method", "source_document", "source_page", "source_url", "captured_at_local", "ocr_review_status", "state"]
        fields = provenance + [x for x in fields if x not in provenance]
        with (OUT_DIR / f"{kind}_all_states.csv").open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
        print(f"{kind}_all_states.csv: {len(rows)} rows")
if __name__ == "__main__":
    main()
