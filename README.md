# E/M Coding Evaluator

A sophisticated AI-powered system for evaluating medical progress notes and optimizing E/M (Evaluation and Management) coding for revenue optimization.

## 🎯 Overview

This system uses **PydanticAI** agents to analyze orthopedic medical progress notes and provide:
- Accurate E/M code assignments (99212-99215)
- Detailed clinical justifications
- Compliance auditing
- Recommendations for appropriate upcoding opportunities

## 🏗️ Architecture

### Two-Stage Agent System

#### Stage D: E/M Enhancement Agent
- Analyzes medical progress notes
- Assigns appropriate E/M codes per AMA 2024 guidelines
- Provides detailed justifications (History, Examination, Medical Decision Making)

#### Stage E: E/M Auditor Agent  
- Reviews enhanced notes for compliance
- Identifies risk flags
- Produces final billing-ready documentation

### Technology Stack

- **PydanticAI**: AI agent framework with structured outputs
- **Azure Functions**: Serverless orchestration and HTTP endpoints
- **Azure OpenAI**: GPT-4 for medical coding analysis
- **PyMuPDF**: PDF text extraction
- **Python 3.9+**: Core runtime

## 🚀 Quick Start

### 1. Setup
```bash
# Install dependencies
python setup.py

# Configure Azure OpenAI credentials in local.settings.json
{
  "Values": {
    "AZURE_OPENAI_ENDPOINT": "https://your-resource.openai.azure.com/",
    "AZURE_OPENAI_KEY": "your-key",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4"
  }
}
```

### 2. Run Locally
```bash
# Start Azure Functions runtime
func start

# Test with sample data
curl http://localhost:7071/api/test_samples?limit=10
```

### 3. Process Documents

#### Single Document
```bash
curl -X POST http://localhost:7071/api/em_coding \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "123",
    "date_of_service": "2024-01-15",
    "provider": "Dr. Smith",
    "text": "Patient presents with knee pain..."
  }'
```

#### Batch Processing
```bash
curl -X POST http://localhost:7071/api/em_coding \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "document_id": "123",
        "date_of_service": "2024-01-15", 
        "provider": "Dr. Smith",
        "text": "Patient presents with knee pain..."
      }
    ]
  }'
```

## 📊 Expected Output

The system generates Excel reports with these columns per the PRD:

1. **Document ID**: Unique identifier
2. **Date of Service**: Service date
3. **Provider**: Healthcare provider name
4. **E&M Code 99212**: Recommendations for this code level
5. **E&M Code 99213**: Recommendations for this code level  
6. **E&M Code 99214**: Recommendations for this code level
7. **E&M Code 99215**: Recommendations for this code level

### Sample Response
```json
{
  "status": "success",
  "result": {
    "document_id": "123",
    "enhancement_result": {
      "code": "99214",
      "justifications": "History: Detailed history with review of systems... Examination: Detailed musculoskeletal exam... Medical Decision Making: Moderate complexity with multiple diagnostic options..."
    },
    "audit_result": {
      "audit_flags": [],
      "final_note": "Enhanced provider note ready for billing..."
    }
  }
}
```

## 🧪 Testing

### Test Individual Agents
```bash
# Test with sample PDFs
python test_agents.py

```

### Process Sample Data
The system includes ~1000 sample PDF files in `data/samples/` for testing and validation.

## 🛠️ Development

### Project Structure
```
mko_em_evaluator/
├── function_app.py              # Azure Functions entry point
├── models/
│   └── pydantic_models.py      # PydanticAI agents and schemas
├── subagents/
│   ├── em_enhancement_agent.py # Stage D agent
│   └── em_auditor_agent.py     # Stage E agent  
├── orchestrator/

├── data/
│   ├── pdf_processor.py        # PDF text extraction
│   └── samples/                # Sample PDF files
└── tests/                      # Unit and integration tests
```

### Key Components

#### PydanticAI Agents
- **em_enhancement_agent**: Assigns E/M codes with clinical justifications
- **em_auditor_agent**: Reviews for compliance and finalizes documentation

#### Models
- **EMInput**: Input schema for progress notes
- **EMCodeAssignment**: Structured output for code assignment
- **EMAuditResult**: Structured output for audit review

## 🔧 Configuration

### Required Environment Variables
```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-key  
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-10-21
```

### Optional Configuration
```bash
# For advanced PDF processing
AZURE_FORM_RECOGNIZER_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_FORM_RECOGNIZER_KEY=your-key
```

## 📈 Performance & Scalability

- **Concurrent Processing**: Configurable semaphore limits (default: 5 concurrent docs)
- **Batch Processing**: Handles multiple documents efficiently
- **Error Handling**: Robust error handling with detailed logging
- **Azure Functions**: Auto-scaling serverless execution

## 🔒 Compliance & Security

- **HIPAA Considerations**: No PHI stored, in-memory processing only
- **Azure Key Vault**: Recommended for credential management
- **Audit Trails**: Comprehensive logging for compliance
- **Structured Outputs**: Consistent, validated response formats

## 🎯 Roadmap

### Phase 1 (Current)
- ✅ PydanticAI agent implementation
- ✅ PDF processing capabilities
- ✅ Azure Functions orchestration
- ✅ Basic testing framework

### Phase 2 (Next)
- [ ] Advanced PDF processing with Form Recognizer
- [ ] Excel export functionality
- [ ] ROI analysis and reporting
- [ ] Integration with existing systems

### Phase 3 (Future) 
- [ ] Real-time progress note enhancement
- [ ] Machine learning model fine-tuning
- [ ] Advanced analytics dashboard
- [ ] Multi-specialty support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is proprietary to MKO and Proactive Medical Solutions.

---

**Contact**: For questions or support, please contact the development team.
