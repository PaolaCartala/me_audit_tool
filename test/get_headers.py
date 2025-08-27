#!/usr/bin/env python3
import os
import re
import pdfplumber

# Patrón principal para buscar "Apellido, Nombre (con opcional inicial) MM/DD/YYYY #ID"
PATTERN = re.compile(
    r"(?P<name>[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ-]+,\s*[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ\s]+?)\s+"
    r"(?P<date>\d{2}/\d{2}/\d{4})\s+#(?P<id>\d+)",
    re.IGNORECASE
)

# Patrones de diagnóstico
DATE_RE = re.compile(r"\d{2}/\d{2}/\d{4}")
ID_RE = re.compile(r"#(?P<id>\d+)")


def get_headers(limit=5, folder_path="data/samples", header_lines=5):
    """
    Extrae las primeras `header_lines` líneas del texto de la primera página
    de hasta `limit` archivos PDF en `folder_path`.
    Devuelve una lista de tuplas: (filename, header_text, name, id, diagnostics).
    diagnostics es un dict con claves 'has_date', 'has_id', 'name_tokens'.
    """
    headers = []
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
    for pdf_file in pdf_files[:limit]:
        pdf_path = os.path.join(folder_path, pdf_file)
        with pdfplumber.open(pdf_path) as pdf:
            text = pdf.pages[0].extract_text() or ""
        header_text = "\n".join(text.splitlines()[:header_lines])
        match = PATTERN.search(header_text)
        if match:
            name = match.group("name").strip()
            pid = match.group("id").strip()
            diagnostics = {}
        else:
            name, pid = None, None
            # Diagnóstico del porqué no hizo match
            has_date = bool(DATE_RE.search(header_text))
            id_m = ID_RE.search(header_text)
            has_id = bool(id_m)
            # Extraer tokens de la línea del nombre (primera línea)
            first_line = header_text.splitlines()[0] if header_text else ""
            name_tokens = re.findall(r"[\wÁÉÍÓÚÑ-]+", first_line)
            diagnostics = {
                "has_date": has_date,
                "has_id": has_id,
                "name_tokens": name_tokens
            }
        headers.append((pdf_file, header_text, name, pid, diagnostics))
    return headers


if __name__ == "__main__":
    results = get_headers(limit=963, header_lines=5)
    for filename, header_text, name, pid, diag in results:
        print(f"{filename}:")
        print("Header:")
        print(header_text)
        if name and pid:
            print(f"Extracted -> {name},{pid}")
        else:
            print("Extracted -> None")
            print("Diagnostics:")
            print(f"  has_date: {diag['has_date']}")
            print(f"  has_id: {diag['has_id']}")
            print(f"  name_tokens: {diag['name_tokens']}")
            print("  Reason: posiblemente nombre con inicial media o guiones, revisar tokens o ajustar regex.")
        print("-" * 40)
