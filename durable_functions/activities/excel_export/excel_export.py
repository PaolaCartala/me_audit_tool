import pandas as pd
import logging

def main(results: list) -> str:
    """
    Activity function: receives a list of evaluation results and returns an Excel file as a base64 string
    """
    try:
        # Build DataFrame for Excel export
        rows = []
        for r in results:
            rows.append({
                "Document ID": r.get("document_id"),
                "Date of Service": r.get("date_of_service"),
                "Provider": r.get("provider"),
                "E&M Code 99212": r.get("recommendations", {}).get("99212", ""),
                "E&M Code 99213": r.get("recommendations", {}).get("99213", ""),
                "E&M Code 99214": r.get("recommendations", {}).get("99214", ""),
                "E&M Code 99215": r.get("recommendations", {}).get("99215", "")
            })
        df = pd.DataFrame(rows)
        # Export to Excel in-memory
        from io import BytesIO
        import base64
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        b64_excel = base64.b64encode(output.read()).decode("utf-8")
        return b64_excel
    except Exception as e:
        logging.error(f"Excel export error: {str(e)}")
        return ""
