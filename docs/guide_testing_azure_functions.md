# Testing Guide - EM Audit Tool Azure Durable Functions

## 🆕 New Features (August 2025)

### Enhanced Auditor Agent with Advanced Confidence Scoring System

#### 🎯 Confidence Assessment Object
The auditor agent now returns a comprehensive confidence assessment with:
- **Score**: Integer from 0-100 indicating auditor certainty
- **Tier**: Confidence level label (Very High, High, Moderate, Low, Very Low)
- **Reasoning**: Bulleted explanation of confidence factors
- **Score Deductions**: Specific reasons why score is not 100 (if applicable)

#### 📊 Confidence Tiers
- **90-100 (Very High)**: Clear, unambiguous documentation fully supports the assigned code
- **70-89 (High)**: Good documentation supports the code with minor gaps or ambiguities  
- **50-69 (Moderate)**: Reasonable support for the code but some uncertainties or missing elements
- **30-49 (Low)**: Limited support, significant gaps, or borderline between codes
- **0-29 (Very Low)**: Poor documentation, major gaps, or conflicting evidence

#### 🔧 Enhanced Features
- **Structured Reasoning**: Bulleted lists showing factors that increase/decrease confidence
- **Explicit Deductions**: Specific point deductions with explanations
- **UI-Ready Labels**: Tier labels for frontend display
- **Compliance Focus**: More thorough audit flags and documentation gaps detection

## Available URLs
- **Health Check**: `https://audit-tool-g0bvdmfwgqc7gagu.eastus-01.azurewebsites.net/api/health`
- **Start Orchestration from Samples**: `https://audit-tool-g0bvdmfwgqc7gagu.eastus-01.azurewebsites.net/api/orchestrations/from-samples`
- **Download Excel Report**: `https://audit-tool-g0bvdmfwgqc7gagu.eastus-01.azurewebsites.net/api/reports/excel/{instance_id}`
- **Download JSON Report**: `https://audit-tool-g0bvdmfwgqc7gagu.eastus-01.azurewebsites.net/api/reports/json/{instance_id}`

## Step-by-Step Testing Process

### 1. Check Application Health
```http
GET https://audit-tool-g0bvdmfwgqc7gagu.eastus-01.azurewebsites.net/api/health
```
**Expected response**: Status 200 with health message

### 2. Start Processing 2 Documents
```http
POST https://audit-tool-g0bvdmfwgqc7gagu.eastus-01.azurewebsites.net/api/orchestrations/from-samples?limit=2
Content-Type: application/json
```

**Expected response**: Status 202 with a structure similar to:
```json
{
    "id": "abc123...",
    "statusQueryGetUri": "https://audit-tool-g0bvdmfwgqc7gagu.eastus-01.azurewebsites.net/runtime/webhooks/durabletask/instances/abc123.../",
    "sendEventPostUri": "https://audit-tool-g0bvdmfwgqc7gagu.eastus-01.azurewebsites.net/runtime/webhooks/durabletask/instances/abc123.../raiseEvent/{eventName}",
    "terminatePostUri": "https://audit-tool-g0bvdmfwgqc7gagu.eastus-01.azurewebsites.net/runtime/webhooks/durabletask/instances/abc123.../terminate",
    "rewindPostUri": "https://audit-tool-g0bvdmfwgqc7gagu.eastus-01.azurewebsites.net/runtime/webhooks/durabletask/instances/abc123.../rewind",
    "purgeHistoryDeleteUri": "https://audit-tool-g0bvdmfwgqc7gagu.eastus-01.azurewebsites.net/runtime/webhooks/durabletask/instances/abc123.../history"
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
GET https://audit-tool-g0bvdmfwgqc7gagu.eastus-01.azurewebsites.net/api/reports/{instance_id}
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
- Confidence Score (0-100)
- Confidence Tier (Very High/High/Moderate/Low/Very Low)
- Confidence Reasoning (Bulleted explanation)
- Score Deductions (Specific point reductions)
- Audit Flags Count
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
GET https://audit-tool-g0bvdmfwgqc7gagu.eastus-01.azurewebsites.net/api/reports/json/{instance_id}
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
                "confidence": {
                    "score": 85,
                    "tier": "High",
                    "reasoning": "FACTORS INCREASING CONFIDENCE:\n- Comprehensive documentation of chronic conditions\n- Clear medical decision making elements\n- Well-documented physical examination\n- Appropriate time documentation\n\nFACTORS DECREASING CONFIDENCE:\n- External data review not explicitly documented\n- Some laboratory values mentioned but not detailed",
                    "score_deductions": [
                        "- Score reduced by 10 points: External data review not explicitly documented",
                        "- Score reduced by 5 points: Laboratory results mentioned but values not specified"
                    ]
                },
                "code_evaluations": {
                    "code_99212_evaluation": "...",
                    "code_99213_evaluation": "...",
                    "code_99214_evaluation": "...",
                    "code_99215_evaluation": "..."
                }
            },
            "timestamp": "2025-07-03T...",
            "processing_metadata": {
                "enhancement_agent_model": "Azure OpenAI GPT-5",
                "auditor_agent_model": "Azure OpenAI GPT-5",
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
   - `baseUrl`: `https://audit-tool-g0bvdmfwgqc7gagu.eastus-01.azurewebsites.net`
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

## 🚀 Deployment Commands

### Azure login
```bash
az login
```

### Reset Deployment (Clean Start)
```bash
az functionapp restart --name audit-tool --resource-group AppliedAI
```

### Publish/Deploy
```bash
func azure functionapp publish audit-tool --force
```

### Verify Deployment
After deployment, test the health endpoint:
```bash
curl https://audit-tool-g0bvdmfwgqc7gagu.eastus-01.azurewebsites.net/api/health
```

