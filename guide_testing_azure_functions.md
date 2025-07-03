# Testing Guide - EM Audit Tool Azure Durable Functions

## Available URLs
- **Health Check**: `https://audit-tool-emdvhafpa6h6h5fj.eastus2-01.azurewebsites.net/api/health`
- **Start Orchestration from Samples**: `https://audit-tool-emdvhafpa6h6h5fj.eastus2-01.azurewebsites.net/api/orchestrations/from-samples`
- **Download Excel Report**: `https://audit-tool-emdvhafpa6h6h5fj.eastus2-01.azurewebsites.net/api/reports/excel/{instance_id}`
- **Download JSON Report**: `https://audit-tool-emdvhafpa6h6h5fj.eastus2-01.azurewebsites.net/api/reports/json/{instance_id}`

## Step-by-Step Testing Process

### 1. Check Application Health
```http
GET https://audit-tool-emdvhafpa6h6h5fj.eastus2-01.azurewebsites.net/api/health
```
**Expected response**: Status 200 with health message

### 2. Start Processing 2 Documents
```http
POST https://audit-tool-emdvhafpa6h6h5fj.eastus2-01.azurewebsites.net/api/orchestrations/from-samples?limit=2
Content-Type: application/json
```

**Expected response**: Status 202 with a structure similar to:
```json
{
    "id": "abc123...",
    "statusQueryGetUri": "https://audit-tool-emdvhafpa6h6h5fj.eastus2-01.azurewebsites.net/runtime/webhooks/durabletask/instances/abc123.../",
    "sendEventPostUri": "https://audit-tool-emdvhafpa6h6h5fj.eastus2-01.azurewebsites.net/runtime/webhooks/durabletask/instances/abc123.../raiseEvent/{eventName}",
    "terminatePostUri": "https://audit-tool-emdvhafpa6h6h5fj.eastus2-01.azurewebsites.net/runtime/webhooks/durabletask/instances/abc123.../terminate",
    "rewindPostUri": "https://audit-tool-emdvhafpa6h6h5fj.eastus2-01.azurewebsites.net/runtime/webhooks/durabletask/instances/abc123.../rewind",
    "purgeHistoryDeleteUri": "https://audit-tool-emdvhafpa6h6h5fj.eastus2-01.azurewebsites.net/runtime/webhooks/durabletask/instances/abc123.../history"
}
```

**Important**: Save the `id` and `statusQueryGetUri` for the next steps.

### 3. Monitor Orchestration Status
```http
GET {statusQueryGetUri}
```

Repeat this call every 30-60 seconds until the status is `"Completed"`.

**Possible statuses**:
- `"Running"`: The orchestration is in progress
- `"Completed"`: The orchestration finished successfully
- `"Failed"`: The orchestration failed
- `"Terminated"`: The orchestration was manually terminated

**Response when completed**:
```json
{
    "name": "em_coding_orchestrator",
    "instanceId": "abc123...",
    "runtimeStatus": "Completed",
    "input": [...],
    "customStatus": null,
    "output": {
        "processed_documents": 2,
        "successful_documents": 2,
        "failed_documents": 0,
        "processing_timestamp": "2025-07-03T...",
        "results": [...],
        "excel_report_base64": "..."
    },
    "createdTime": "2025-07-03T...",
    "lastUpdatedTime": "2025-07-03T..."
}
```

### 4. Download Excel File
```http
GET https://audit-tool-emdvhafpa6h6h5fj.eastus2-01.azurewebsites.net/api/reports/{instance_id}
```

Replace `{instance_id}` with the ID obtained in step 2.

**Expected response**: 
- Status 200
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- The file will be downloaded as `audit_report_{instance_id}.xlsx`

**Excel columns**:
- Document ID
- Date of Service
- Provider
- Assigned Code
- E&M Code 99212
- E&M Code 99212 evaluation
- E&M Code 99213
- E&M Code 99213 evaluation
- E&M Code 99214
- E&M Code 99214 evaluation
- E&M Code 99215
- E&M Code 99215 evaluation

### 5. Download Consolidated JSON File
```http
GET https://audit-tool-emdvhafpa6h6h5fj.eastus2-01.azurewebsites.net/api/reports/json/{instance_id}
```

**Expected response**: 
- Status 200
- Content-Type: `application/json`
- The file will be downloaded as `audit_results_consolidated_{instance_id}.json`

**JSON structure**:
```json
{
    "test_summary": {
        "total_documents": 2,
        "successful_documents": 2,
        "failed_documents": 0,
        "test_timestamp": "2025-07-03T...",
        "test_type": "azure_durable_functions_processing",
        "instance_id": "abc123..."
    },
    "results": [
        {
            "document_id": "...",
            "date_of_service": "...",
            "provider": "...",
            "original_text_length": 1234,
            "original_text_preview": "...",
            "enhancement_agent": {
                "assigned_code": "99213",
                "justification": "...",
                "code_recommendations": {
                    "code_99212": "...",
                    "code_99213": "...",
                    "code_99214": "...",
                    "code_99215": "..."
                }
            },
            "auditor_agent": {
                "final_assigned_code": "99213",
                "final_justification": "...",
                "audit_flags": [],
                "billing_ready_note": "...",
                "final_code_recommendations": {
                    "code_99212": "...",
                    "code_99213": "...",
                    "code_99214": "...",
                    "code_99215": "..."
                }
            },
            "timestamp": "2025-07-03T...",
            "processing_metadata": {
                "enhancement_agent_model": "Azure OpenAI GPT-4.1",
                "auditor_agent_model": "Azure OpenAI GPT-4.1",
                "processing_time": "2025-07-03T..."
            }
        }
    ]
}
```

## Common Error Cases

### Error 404 - Instance Not Found
If you get a 404 when downloading reports, check:
- That the `instance_id` is correct
- That the orchestration has completed successfully

### Error 500 - Function Load Error
If you get 500 errors, check:
- The Azure Functions logs in the portal
- That all binding types are consistent
- That all dependencies are installed correctly

### Error 202 - Orchestration Not Completed
If you try to download reports before completion:
- Keep monitoring the status
- Wait until the status is "Completed"

## Tips for Testing in Postman

1. **Set Up Environment Variables**:
   - `baseUrl`: `https://audit-tool-emdvhafpa6h6h5fj.eastus2-01.azurewebsites.net`
   - `instanceId`: Automatically saved after step 2
   - `statusQueryGetUri`: Automatically saved after step 2

2. **Automatic Test Scripts**:
   In the "Start Orchestration from Samples" request, add this script in the "Tests" tab:
   ```javascript
   if (pm.response.code === 202) {
       const responseBody = pm.response.json();
       pm.environment.set('instanceId', responseBody.id);
       pm.environment.set('statusQueryGetUri', responseBody.statusQueryGetUri);
       console.log('Instance ID saved:', responseBody.id);
   }
   ```

3. **Import Collection**:
   Import the `EM_Audit_Tool_Postman_Collection.json` file into Postman to have all requests preconfigured.

## Estimated Processing Time

- **2 documents**: 2-5 minutes
- **5 documents**: 5-10 minutes
- **10 documents**: 10-15 minutes

Processing time depends on:
- Document length
- Complexity of medical content
- Azure OpenAI service load

