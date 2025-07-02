import os
import glob
import json

import pandas as pd


folder = 'test_results'
json_paths = glob.glob(os.path.join(folder, '*.json'))

rows = []

for path in json_paths:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    rec = {
        'Document ID': data.get('document_id'),
        'Date of Service': data.get('date_of_service'),
        'Provider': data.get('provider'),
    }
    for code in ['99212', '99213', '99214', '99215']:
        enh_key = f'code_{code}'
        enh_text = data.get('enhancement_agent', {}) \
                       .get('code_recommendations', {}) \
                       .get(enh_key, '')
        rec[f'E&M Code {code}'] = enh_text
        
        aud_text = data.get('auditor_agent', {}) \
                       .get('final_code_recommendations', {}) \
                       .get(enh_key, '')
        rec[f'E&M Code {code} evaluation'] = aud_text
    rows.append(rec)

df = pd.DataFrame(rows)
output_path = os.path.join(folder, 'combined_results.xlsx')
df.to_excel(output_path, index=False)
print(f"✅ Excel file generated in: {output_path}")
