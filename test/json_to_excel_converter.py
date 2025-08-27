import os
import glob
import json
import re

import pandas as pd
from datetime import datetime


def clean_text_for_excel(text):
    """
    Clean text to remove characters that Excel cannot handle
    """
    if not isinstance(text, str):
        return text
    
    # Remove or replace illegal XML characters that Excel can't handle
    # Excel uses XML internally and these characters cause issues
    illegal_chars = [
        '\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08',
        '\x0B', '\x0C', '\x0E', '\x0F', '\x10', '\x11', '\x12', '\x13', '\x14',
        '\x15', '\x16', '\x17', '\x18', '\x19', '\x1A', '\x1B', '\x1C', '\x1D',
        '\x1E', '\x1F'
    ]
    
    # Remove illegal characters
    for char in illegal_chars:
        text = text.replace(char, '')
    
    # Replace some common problematic characters
    text = text.replace('\x0B', ' ')  # Vertical tab
    text = text.replace('\x0C', ' ')  # Form feed
    text = text.replace('\x1F', ' ')  # Unit separator
    
    # Remove any remaining control characters (except \n, \r, \t)
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
    
    # Limit cell content length (Excel has a limit of ~32,767 characters per cell)
    if len(text) > 32000:
        text = text[:32000] + "... [truncated]"
    
    return text


# folder = 'data/completed/35_test/test_results_jsons_new'
folder = 'test_results'
json_paths = glob.glob(os.path.join(folder, 'result_*.json'))

rows = []

for path in json_paths:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Format evaluation with audit information
    auditor_data = data.get('auditor_agent', {})
    final_justification_obj = auditor_data.get('final_justification', {})
    audit_flags = auditor_data.get('audit_flags', [])
    
    # Create formatted evaluation text
    evaluation_parts = []
    
    # Handle structured final_justification
    if isinstance(final_justification_obj, dict):
        if final_justification_obj.get('supportedBy'):
            evaluation_parts.append(f"Code Selection: {final_justification_obj['supportedBy']}")
        
        if final_justification_obj.get('documentationSummary'):
            doc_summary = '\n'.join([f"  • {item}" for item in final_justification_obj['documentationSummary']])
            evaluation_parts.append(f"Documentation Summary:\n{doc_summary}")
            
        if final_justification_obj.get('mdmConsiderations'):
            mdm_considerations = '\n'.join([f"  • {item}" for item in final_justification_obj['mdmConsiderations']])
            evaluation_parts.append(f"MDM Considerations:\n{mdm_considerations}")
            
        if final_justification_obj.get('complianceAlerts'):
            compliance_alerts = '\n'.join([f"  ⚠ {item}" for item in final_justification_obj['complianceAlerts']])
            evaluation_parts.append(f"Compliance Alerts:\n{compliance_alerts}")
    elif isinstance(final_justification_obj, str) and final_justification_obj:
        # Handle legacy string format for backward compatibility
        evaluation_parts.append(f"Justification: {final_justification_obj}")
    
    if audit_flags:
        flags_text = '\n'.join([f"  • {flag}" for flag in audit_flags])
        evaluation_parts.append(f"Audit Flags:\n{flags_text}")
    rec = {
        'Document ID': clean_text_for_excel(data.get('document_id')),
        'Patient Name': clean_text_for_excel(data.get('patient_name', 'Unknown Patient')),
        'Patient ID': clean_text_for_excel(data.get('patient_id', '0000')),
        'Date of Service': clean_text_for_excel(data.get('date_of_service')),
        'Provider': clean_text_for_excel(data.get('provider')),
        'Assigned Code': clean_text_for_excel(data.get('enhancement_agent', {}).get('assigned_code', '')),
        'E&M Code Justification': clean_text_for_excel(data.get('enhancement_agent', {}).get('justification', '')),
        'E&M Code Evaluation': clean_text_for_excel('\n\n'.join(evaluation_parts))
    }
    for code in ['99212', '99213', '99214', '99215']:
        enh_key = f'code_{code}'
        eval_key = f'code_{code}_evaluation'
        
        # enhancement recommendations
        enh_text = data.get('enhancement_agent', {}) \
                       .get('code_recommendations', {}) \
                       .get(enh_key, '')
        rec[f'E&M Code {code}'] = clean_text_for_excel(enh_text)
        
        # auditor evaluations
        eval_text = data.get('auditor_agent', {}) \
                        .get('code_evaluations', {}) \
                        .get(eval_key, '')
        rec[f'E&M Code {code} evaluation'] = eval_text
        
    rows.append(rec)

df = pd.DataFrame(rows)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_path = os.path.join(folder, f'combined_results_{timestamp}.xlsx')
df.to_excel(output_path, index=False)
print(f"✅ Excel file generated in: {output_path}")
