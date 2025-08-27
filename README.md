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

## Environment-Based Deployment

This project includes automated deployment scripts for different environments using Make and Bash.

### Environment Configuration

The project supports two environments:

- **Development Environment** (`.env.development`)
- **Production Environment** (`.env.production`)

### Deployment Commands

#### Quick Deployment

Deploy to **Development**:
```bash
make dev
```

Deploy to **Production**:
```bash
make prod
```

#### Manual Environment Setup

Set up development environment:
```bash
make setup-dev
# or
./setup-env.sh dev
```

Set up production environment:
```bash
make setup-prod
# or
./setup-env.sh prod
```

#### Available Make Commands

```bash
make help        # Show all available commands
make dev         # Deploy to development (audit-tool-dev)
make prod        # Deploy to production (audit-tool)
make setup-dev   # Setup dev environment only (no deploy)
make setup-prod  # Setup prod environment only (no deploy)
```

### Deployment Process

Each deployment command automatically:

1. **Checks Azure Login**: Verifies if you're logged into Azure CLI (runs `az login` if needed)
2. **Environment Setup**: Copies the appropriate `.env` file (development or production)
3. **Function App Restart**: Restarts the target Azure Function App
4. **Code Deployment**: Publishes the latest code using Azure Functions Core Tools

### Prerequisites for Deployment

- Azure CLI installed and configured
- Azure Functions Core Tools v4
- Proper permissions for the target resource group (`AppliedAI`)
- Access to both function apps (`audit-tool` and `audit-tool-dev`)

## �📊 API Endpoints

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
├── __init__.py                     # Package initialization
├── constants.py                    # Application constants
├── function_app.py                 # Main Azure Functions app configuration
├── host.json                       # Azure Functions host configuration
├── settings.py                     # Application settings and logger config
├── requirements.txt                # Python dependencies
├── local.settings.json             # Local development settings
├── LICENSE                         # Project license
├── README.md                       # Project documentation
├── Makefile                        # Deployment automation
├── setup-env.sh                    # Environment setup script
├── .env.development                # Development environment variables
├── .env.production                 # Production environment variables
├── agents/                         # AI agent implementations
│   ├── __init__.py
│   ├── em_auditor_agent.py         # Core auditor agent
│   ├── em_enhancement_agent.py     # Enhancement agent
│   ├── em_progress_note_agent.py   # Progress note agent
│   ├── optimized_em_auditor_agent.py    # Optimized auditor version
│   ├── optimized_em_enhancement_agent.py # Optimized enhancement version
│   ├── models/                     # Agent data models
│   └── prompts/                    # Agent prompt templates
├── data/                           # Sample data and test files
│   ├── __init__.py
│   ├── pdf_processor.py            # PDF processing utilities
│   ├── patient_intake.json         # Sample patient data
│   ├── checkoutsheet_*.json        # Sample checkout sheets
│   ├── dictation_success_*.json    # Sample dictation data
│   ├── 35_test/                    # Test dataset (35 samples)
│   ├── 500_data/                   # Large test dataset (500 samples)
│   ├── 500_run_0707/              # Test run results
│   ├── completed/                  # Processed samples
│   └── samples/                    # Sample input files
├── docs/                           # Documentation
│   ├── CONFIDENCE_TIERS.md         # Confidence scoring documentation
│   ├── guide_testing_azure_functions.md # Testing guide
│   └── user_feedback_system.md     # User feedback system docs
├── durable_functions/              # Azure Durable Functions
│   ├── __init__.py
│   ├── auditor_agent_activity/     # Auditor agent activity function
│   ├── download_json_report/       # JSON report download function
│   ├── download_report/            # Excel report download function
│   ├── em_coding_orchestrator/     # Main orchestrator function
│   ├── em_progress_note_orchestrator/ # Progress note orchestrator
│   ├── enhancement_agent_activity/ # Enhancement agent activity
│   ├── excel_export_activity/      # Excel export activity
│   ├── get_feedback_analytics/     # Feedback analytics function
│   ├── health/                     # Health check function
│   ├── progress_note_agent_activity/ # Progress note agent activity
│   ├── start_orchestration_from_body/ # Start orchestration from request body
│   ├── start_orchestration_from_samples/ # Start orchestration from samples
│   ├── progress_note_from_id/      # Start progress note processing
│   └── submit_feedback/            # User feedback submission
├── guidelines/                     # Medical coding guidelines
│   ├── ama_em_guideline.pdf        # AMA E/M guidelines (PDF)
│   └── em_guideline.md             # E/M guidelines (Markdown)
├── run_tests/                      # Test execution and results
│   ├── 500_run.zip                 # Archived test runs
│   ├── combined_results_*.xlsx     # Combined test results
│   ├── test_results_*.json         # JSON test results
│   └── 500_run/                    # Individual test run data
├── services/                       # Business logic services
│   ├── __init__.py
│   └── feedback_service.py         # User feedback service
├── test/                           # Test scripts and utilities
│   ├── __init__.py
│   ├── diagnose_mcp.py             # MCP diagnostic tools
│   ├── get_headers.py              # HTTP header testing
│   ├── json_to_excel_converter.py  # Data conversion utilities
│   ├── test_agent.py               # Agent testing
│   ├── test_enhacement_new.py      # Enhancement testing
│   ├── test_feedback_endpoints.py  # Feedback API testing
│   ├── test_latency.py             # Performance testing
│   ├── test_optimized_agents.py    # Optimized agent testing
│   └── test_quick.py               # Quick testing script
├── test_results/                   # Test output and results
│   ├── gpt5_result*.json           # GPT-5 test results
│   ├── new_confidence.json         # Confidence system results
│   ├── new_reasoning_*.json        # Reasoning test results
│   ├── optimized_prompts.json      # Prompt optimization results
│   └── result_*.json               # Various test results
└── utils/                          # Utility functions and helpers
    └── ...                         # Utility modules
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
