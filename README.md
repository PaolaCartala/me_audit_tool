# EM Audit Tool - Azure Functions

## 📋 Overview

The EM Audit Tool is an Azure Functions-based solution that automates the auditing and enhancement of medical progress notes for E/M (Evaluation and Management) coding compliance per AMA 2025 guidelines. The system uses AI agents to analyze medical documentation, assign appropriate E/M codes, and provide comprehensive auditing with confidence scoring.

## 🏗️ Architecture

### Core Components

- **Enhancement Agent**: Analyzes medical progress notes and assigns appropriate E/M codes (99212-99215)
- **Auditor Agent**: Reviews enhancement recommendations for compliance and provides final audit results with confidence scoring
- **Orchestrator**: Coordinates the processing workflow using Azure Durable Functions
- **Export Functions**: Generate Excel and JSON reports

### Technology Stack

- **Azure Functions** (Python 3.10)
- **Azure Durable Functions** for workflow orchestration
- **Azure OpenAI** for AI-powered medical coding analysis
- **PydanticAI** for structured AI interactions
- **Pydantic** for data validation and serialization

## 🚀 Features

### ✅ Enhanced Auditing with Advanced Confidence System

- **Confidence Assessment Object**: Comprehensive confidence evaluation with score, tier, reasoning, and deductions
- **Score**: 0-100 integer scale indicating auditor certainty
- **Tier**: UI-friendly labels (Very High, High, Moderate, Low, Very Low)
- **Reasoning**: Bulleted explanation of factors that increase/decrease confidence
- **Score Deductions**: Specific point reductions with explanations (when score < 100)
- **Compliance Flags**: Automatic detection of documentation gaps and risks
- **Billing-Ready Notes**: Enhanced notes optimized for submission

### ✅ Comprehensive E/M Code Analysis

- Support for codes 99212, 99213, 99214, and 99215
- Detailed justifications based on AMA 2025 guidelines
- Recommendations for documentation enhancement
- Code evaluation and compliance assessment

### ✅ Flexible Deployment Options

- Azure Functions deployment
- Local development and testing
- Containerized deployment support
- CI/CD pipeline integration

## 📦 Installation & Setup

### Prerequisites

- Python 3.10+
- Azure Functions Core Tools v4
- Azure CLI
- Azure OpenAI service deployment

### Environment Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd em_audit_tool
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp local.settings.json.example local.settings.json
   # Edit local.settings.json with your Azure OpenAI credentials
   ```

### Required Environment Variables

```json
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsFeatureFlags": "EnableWorkerIndexing",
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "AZURE_OPENAI_ENDPOINT": "https://your-instance.openai.azure.com/",
    "AZURE_OPENAI_KEY": "your-api-key",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "your-deployment-name",
    "AZURE_OPENAI_API_VERSION": "2024-02-15-preview"
  }
}
```

## 💻 Local Development

### Running Locally

1. **Start Azure Functions**:
   ```bash
   func start
   ```

2. **Test endpoints**:
   - Health check: `http://localhost:7071/api/health`
   - Start orchestration: `http://localhost:7071/api/orchestrations/from-samples`

### Quick Testing

Run the enhanced test script:
```bash
python test_quick.py
```

This script now includes confidence score testing and validation.

## 🚀 Deployment

### Reset and Clean Deployment

1. **Reset Azure Functions**:
   ```bash
   func azure functionapp delete <function-app-name> --resource-group <resource-group-name>
   ```

2. **Create new Function App**:
   ```bash
   az functionapp create \
     --resource-group <resource-group-name> \
     --consumption-plan-location <location> \
     --runtime python \
     --runtime-version 3.10 \
     --functions-version 4 \
     --name <function-app-name> \
     --storage-account <storage-account-name>
   ```

### Publish to Azure

1. **Build and deploy**:
   ```bash
   func azure functionapp publish <function-app-name> --python
   ```

2. **Configure application settings**:
   ```bash
   az functionapp config appsettings set \
     --name <function-app-name> \
     --resource-group <resource-group-name> \
     --settings \
     AZURE_OPENAI_ENDPOINT="https://your-instance.openai.azure.com/" \
     AZURE_OPENAI_KEY="your-api-key" \
     AZURE_OPENAI_DEPLOYMENT_NAME="your-deployment-name" \
     AZURE_OPENAI_API_VERSION="2024-02-15-preview"
   ```

### Deployment Commands Summary

```bash
# Reset deployment (optional)
func azure functionapp delete <function-app-name> --resource-group <resource-group-name>

# Publish/Deploy
func azure functionapp publish <function-app-name> --python
```

## 📊 API Endpoints

### Health Check
```http
GET /api/health
```

### Start Processing
```http
POST /api/orchestrations/from-samples?limit=2
```

### Download Reports
```http
GET /api/reports/excel/{instance_id}
GET /api/reports/json/{instance_id}
```

## 🧪 Testing

### Testing Guide
See [Testing Guide](guide_testing_azure_functions.md) for detailed testing instructions.

### Expected Response Structure

```json
{
  "auditor_agent": {
    "final_assigned_code": "99214",
    "final_justification": "...",
    "confidence": {
      "score": 85,
      "tier": "High",
      "reasoning": "FACTORS INCREASING CONFIDENCE:\n- Comprehensive documentation of chronic conditions\n- Clear medical decision making elements\n\nFACTORS DECREASING CONFIDENCE:\n- External data review not explicitly documented",
      "score_deductions": [
        "- Score reduced by 10 points: External data review not explicitly documented",
        "- Score reduced by 5 points: Some laboratory values not detailed"
      ]
    },
    "audit_flags": [],
    "billing_ready_note": "...",
    "code_evaluations": {
      "code_99212_evaluation": "...",
      "code_99213_evaluation": "...",
      "code_99214_evaluation": "...",
      "code_99215_evaluation": "..."
    }
  }
}
```

### Confidence Assessment System

#### Confidence Tiers & Score Ranges
- **90-100 (Very High)**: Clear, unambiguous documentation fully supports the assigned code
- **70-89 (High)**: Good documentation supports the code with minor gaps or ambiguities
- **50-69 (Moderate)**: Reasonable support for the code but some uncertainties or missing elements
- **30-49 (Low)**: Limited support, significant gaps, or borderline between codes
- **0-29 (Very Low)**: Poor documentation, major gaps, or conflicting evidence

#### Enhanced Features
- **Structured Reasoning**: Organized bullets showing confidence factors
- **Explicit Deductions**: Point-by-point score reductions with explanations
- **UI-Ready Labels**: Tier labels for frontend integration
- **Workflow Integration**: Confidence thresholds for auto-approval and review routing

For complete confidence system documentation, see [CONFIDENCE_TIERS.md](CONFIDENCE_TIERS.md).

## 📁 Project Structure

```
em_audit_tool/
├── auditor_agent_activity/          # Auditor agent Azure Function
├── data/                           # Sample data and test files
├── download_json_report/           # JSON report download function
├── download_report/                # Excel report download function
├── em_coding_orchestrator/         # Main orchestrator function
├── enhancement_agent_activity/     # Enhancement agent Azure Function
├── excel_export_activity/          # Excel export activity
├── guidelines/                     # Medical coding guidelines
├── health/                        # Health check function
├── models/                        # Pydantic models and AI agents
├── run_tests/                     # Test results and reports
├── start_orchestration_from_samples/ # Orchestration starter
├── subagents/                     # Core agent implementations
├── test_results/                  # Test output directory
├── utils/                         # Utility functions
├── function_app.py                # Main function app configuration
├── host.json                      # Azure Functions host configuration
├── requirements.txt               # Python dependencies
└── local.settings.json            # Local development settings
```

## 🔧 Configuration

### Host Configuration (host.json)
```json
{
  "version": "2.0",
  "logging": {
    "logLevel": {
      "default": "Information"
    }
  },
  "functionTimeout": "00:10:00",
  "extensions": {
    "durableTask": {
      "hubName": "EMCodingHub",
      "storageProvider": {
        "maxQueuePollingInterval": "00:00:02"
      }
    }
  }
}
```

### Function App Configuration (function_app.py)
The main function app includes:
- HTTP triggers for API endpoints
- Durable function orchestrators
- Activity functions for processing
- Timer triggers for scheduled tasks

## 🔍 Troubleshooting

### Common Issues

1. **Azure OpenAI Connection Issues**:
   - Verify endpoint URL and API key
   - Check deployment name and API version
   - Ensure proper network connectivity

2. **Function Timeout**:
   - Increase `functionTimeout` in host.json
   - Optimize processing for large documents
   - Consider breaking down large batches

3. **Memory Issues**:
   - Monitor memory usage with large document sets
   - Implement document size limits
   - Use streaming for large files

### Debug Mode

Enable detailed logging by setting:
```json
{
  "logging": {
    "logLevel": {
      "default": "Debug"
    }
  }
}
```

## 📈 Performance

### Processing Time Estimates
- **2 documents**: 2-5 minutes
- **5 documents**: 5-10 minutes  
- **10 documents**: 10-15 minutes

### Optimization Tips
- Use embedded guidelines for better performance
- Implement caching for repeated requests
- Monitor Azure OpenAI usage and quotas
- Scale Azure Functions based on workload

## 🔒 Security

### Best Practices
- Store API keys in Azure Key Vault
- Use managed identities when possible
- Implement proper access controls
- Monitor and audit API usage
- Encrypt sensitive data at rest and in transit

## 📋 License

[License information]

## 🤝 Contributing

[Contributing guidelines]

## 📞 Support

[Support contact information]

---

**Last Updated**: August 2025  
**Version**: 2.0.0  
**Features**: Enhanced with Confidence Scoring and Comprehensive Auditing
