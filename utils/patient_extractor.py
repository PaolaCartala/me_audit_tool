import re

import pdfplumber


PATTERN = re.compile(
    r"(?P<name>[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ-]+,\s*[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ\s]+?)\s+"
    r"(?P<date>\d{2}/\d{2}/\d{4})\s+#(?P<id>\d+)",
    re.IGNORECASE
)
DATE_RE = re.compile(r"\d{2}/\d{2}/\d{4}")
ID_RE = re.compile(r"#(?P<id>\d+)")

def get_patient_from_pdf_headers(pdf_path, header_lines=5):
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text() or ""
    header_text = "\n".join(text.splitlines()[:header_lines])
    match = PATTERN.search(header_text)
    if match:
        name = match.group("name").strip()
        pid = match.group("id").strip()
        # diagnostics = {}
    else:
        name, pid = None, None
        # has_date = bool(DATE_RE.search(header_text))
        # id_m = ID_RE.search(header_text)
        # has_id = bool(id_m)
        # first_line = header_text.splitlines()[0] if header_text else ""
        # name_tokens = re.findall(r"[\wÁÉÍÓÚÑ-]+", first_line)
        # diagnostics = {
        #     "has_date": has_date,
        #     "has_id": has_id,
        #     "name_tokens": name_tokens
        # }
    return name, pid
