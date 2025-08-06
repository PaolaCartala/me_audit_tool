import logging
import base64
from io import BytesIO
from typing import List

import pandas as pd


def main(final_results: List[dict]) -> str:
    logging.info("Generating Excel report...")
    try:
        rows = []
        for result in final_results:
            if "error" in result: 
                continue
            
            # Format evaluation with audit information (matching json_to_excel_converter.py)
            auditor_data = result.get('auditor_agent', {})
            final_justification = auditor_data.get('final_justification', '')
            audit_flags = auditor_data.get('audit_flags', [])
            
            # Create formatted evaluation text
            evaluation_parts = []
            if final_justification:
                evaluation_parts.append(f"Justification: {final_justification}")
            if audit_flags:
                flags_text = '\n'.join([f"  {flag}" for flag in audit_flags])
                evaluation_parts.append(f"Audit flags:\n{flags_text}")
            
            rec = {
                'Document ID': result.get('document_id'),
                'Patient Name': result.get('patient_name', 'Unknown Patient'),
                'Patient ID': result.get('patient_id', '0000'),
                'Date of Service': result.get('date_of_service', 'N/A'),
                'Provider': result.get('provider', 'N/A'),
                'Assigned Code': result.get('enhancement_agent', {}).get('assigned_code', ''),
                'E&M Code Justification': result.get('enhancement_agent', {}).get('justification', ''),
                'E&M Code Evaluation': '\n\n'.join(evaluation_parts)
            }
            
            # Add enhancement agent code recommendations and auditor evaluations
            for code in ['99212', '99213', '99214', '99215']:
                enh_key = f'code_{code}'
                eval_key = f'code_{code}_evaluation'
                
                # enhancement recommendations
                enh_text = result.get('enhancement_agent', {}) \
                               .get('code_recommendations', {}) \
                               .get(enh_key, '')
                rec[f'E&M Code {code}'] = enh_text
                
                # auditor evaluations
                eval_text = result.get('auditor_agent', {}) \
                                .get('code_evaluations', {}) \
                                .get(eval_key, '')
                rec[f'E&M Code {code} evaluation'] = eval_text
            
            rows.append(rec)

        if not rows:
            logging.warning("No data available to generate Excel report.")
            return ""

        df = pd.DataFrame(rows)
        output_buffer = BytesIO()
        df.to_excel(output_buffer, index=False, engine='openpyxl')
        output_buffer.seek(0)
        b64_excel = base64.b64encode(output_buffer.read()).decode('utf-8')
        logging.info("Excel report generated successfully.")
        return b64_excel
    except Exception as e:
        logging.error(f"Error generating Excel file: {e}")
        return ""
