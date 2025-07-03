import os
import glob
import json

import pandas as pd
from datetime import datetime


# folder = 'data/completed/35_test/test_results_jsons_new'
folder = 'test_results'
json_paths = glob.glob(os.path.join(folder, 'result_*.json'))

rows = []

for path in json_paths:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Format evaluation with audit information
    auditor_data = data.get('auditor_agent', {})
    # final_assigned_code = auditor_data.get('final_assigned_code', '')
    final_justification = auditor_data.get('final_justification', '')
    audit_flags = auditor_data.get('audit_flags', [])
    
    # Create formatted evaluation text
    evaluation_parts = []
    # if final_assigned_code:
    #     evaluation_parts.append(f"Final assigned code: {final_assigned_code}")
    if final_justification:
        evaluation_parts.append(f"Justification: {final_justification}")
    if audit_flags:
        flags_text = '\n'.join([f"  {flag}" for flag in audit_flags])
        evaluation_parts.append(f"Audit flags:\n{flags_text}")
    rec = {
        'Document ID': data.get('document_id'),
        'Date of Service': data.get('date_of_service'),
        'Provider': data.get('provider'),
        'Assigned Code': data.get('enhancement_agent', {}).get('assigned_code', ''),
        'E&M Code evaluation': '\n\n'.join(evaluation_parts)
    }
    for code in ['99212', '99213', '99214', '99215']:
        enh_key = f'code_{code}'
        eval_key = f'code_{code}_evaluation'
        
        # Get enhancement recommendations
        enh_text = data.get('enhancement_agent', {}) \
                       .get('code_recommendations', {}) \
                       .get(enh_key, '')
        rec[f'E&M Code {code}'] = enh_text
        
        # Get auditor evaluations
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
