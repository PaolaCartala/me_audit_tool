# EM Audit Tool - User Feedback System & Enhanced Output Structure

This system allows capturing and storing user feedback on EM code suggestions for later system optimization, and includes the new structured output format for better provider experience.

## Enhanced Output Structure (Updated August 2025)

### Structured Code Justification

The auditor agent now outputs structured justifications instead of plain text, making the output more provider-friendly and actionable:

```json
{
  "final_justification": {
    "supportedBy": "Supported by straightforward MDM per AMA 2025 E/M guidelines.",
    "documentationSummary": [
      "One self-limited/minor problem",
      "Minimal/no reviewed or analyzed data",
      "Minimal risk",
      "Well-appearing established patient",
      "No current orthopedic or new complaints"
    ],
    "mdmConsiderations": [
      "No prescription medication, data analysis, or significant management decisions present",
      "No time recorded; MDM is sole driver for code selection"
    ],
    "complianceAlerts": [
      "Higher codes would be considered upcoding based on documented MDM and risk level."
    ]
  }
}
```

### Provider-Friendly Code Evaluations

Code evaluations now use a structured, provider-friendly format:

```json
{
  "code_99212_evaluation": {
    "mdmAssignmentReason": [
      "Single established patient with straightforward chronic condition management",
      "No new diagnostic tests ordered or complex data analysis required", 
      "Minimal risk assessment with stable patient condition",
      "Standard follow-up care with no medication changes"
    ],
    "documentationEnhancementOpportunities": [
      "Include more detail in physical examination findings",
      "Add functional assessment of patient's condition",
      "Document any patient education or counseling provided"
    ],
    "scoring_impact": "- -5 points: History/physical exam lacks specificity\n- -2 points: PMH contains unrelated issues not addressed",
    "quick_tip": "Even if a problem is unrelated, stating 'not addressed at this visit' can remove ambiguity for coders and auditors."
  }
}
```

## User Feedback System Architecture

### Main Components

1. **Models** (`models/feedback_models.py`):
   - `UserFeedbackRequest`: Model for user feedback requests
   - `UserFeedbackEntity`: Model for entities stored in Azure Tables

2. **Services** (`services/feedback_service.py`):
   - `FeedbackStorageService`: Service for storing and querying feedback in Azure Tables

3. **Endpoints**:
   - `POST /api/feedback`: Endpoint to submit feedback
   - `GET /api/feedback/analytics`: Endpoint to query analytics

### ✨ System Features:
- **Automatic timestamp**: `userActionTimestamp` is automatically generated when creating the Azure Table entity
- **Robust validations**: Pydantic V2 with `@field_validator`
- **Standard HTTP Status**: Using Python's `http.HTTPStatus`
- **Centralized configuration**: Constants and Enums for better maintenance

## Azure Tables Partitioning Strategy

### Partition Key and Row Key

**Partition Key**: `user_id` (MKO user GUID)
- Groups all feedback from a user in the same partition
- Enables efficient queries by user
- Scales well with many different users

**Row Key**: `{timestamp}_{suggested_em_code}_{uuid4()}`
- Guarantees uniqueness using timestamp + EM code + UUID
- Allows natural chronological ordering
- Facilitates time-range queries

### Advantages of this strategy

1. **Efficient queries by user**: All entries from a user are in the same partition
2. **Temporal ordering**: The row key allows sorting by timestamp
3. **Scalability**: Each user is a separate partition
4. **Guaranteed uniqueness**: Combination of timestamp and UUID prevents duplicates

## API Endpoints

### POST /api/feedback

Submits user feedback on an EM code suggestion.

**Request Body**:
```json
{
    "suggestedEmCode": "99213",
    "currentEmCode": "99212",
    "finalEmCode": "99213", 
    "userAction": "accepted",
    "rejectReason": null,
    "userId": "123e4567-e89b-12d3-a456-426614174000",
    "confidenceScore": 0.85,
    "rawAgentResult": {
        "analysis": "Patient meets criteria for 99213",
        "decision_factors": ["History", "Examination", "MDM"]
    }
}
```

**Note**: `userActionTimestamp` is automatically generated server-side and should not be included in the payload.

**Response** (201 Created):
```json
{
    "partition_key": "123e4567-e89b-12d3-a456-426614174000",
    "row_key": "20250811_103000_123456_99213_abc12345",
    "status": "success", 
    "message": "Feedback stored successfully"
}
```

### GET /api/feedback/analytics

Queries feedback analytics for optimization.

**Query Parameters**:
- `user_id`: User ID (GUID)
- `em_code`: Specific EM code  
- `limit`: Results limit (optional)

**Examples**:
```
GET /api/feedback/analytics?user_id=123e4567-e89b-12d3-a456-426614174000
GET /api/feedback/analytics?em_code=99213&limit=50
```

**Response** (200 OK):
```json
{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "count": 15,
    "feedback_entries": [
        {
            "PartitionKey": "123e4567-e89b-12d3-a456-426614174000",
            "RowKey": "20250811_103000_123456_99213_abc12345",
            "SuggestedEmCode": "99213",
            "UserAction": "accepted",
            "ConfidenceScore": 0.85,
            "SystemTimestamp": "2025-08-11T10:30:00Z"
        }
    ]
}
```

## Environment Variables

Add to your `.env`:
```bash
# Azure Storage Configuration for Feedback
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
FEEDBACK_TABLE_NAME=UserFeedback
```

## Usage for Optimization

The stored data can be used for:

1. **Accuracy analysis**: Compare `suggestedEmCode` vs `finalEmCode`
2. **Rejection patterns**: Analyze `rejectReason` to improve the system
3. **Confidence vs accuracy**: Correlation between `confidenceScore` and `userAction`
4. **User patterns**: Identify users with high/low satisfaction
5. **EM code patterns**: Identify problematic codes
