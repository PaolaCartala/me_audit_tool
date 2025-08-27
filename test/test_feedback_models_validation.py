"""Test validation for feedback models after removing userActionTimestamp from request."""

import json
from datetime import datetime

from agents.models.feedback_models import UserFeedbackRequest, UserFeedbackEntity
from constants import UserAction


def test_feedback_request_without_timestamp():
    """Test that UserFeedbackRequest works without userActionTimestamp."""
    print("Testing UserFeedbackRequest without userActionTimestamp...")
    
    # Test data without userActionTimestamp
    test_data = {
        "suggested_em_code": "99213",
        "current_em_code": "99212",
        "final_em_code": "99213",
        "user_action": "accepted",
        "reject_reason": None,
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "confidence_score": 0.85,
        "raw_agent_result": {
            "analysis": "Patient meets criteria for 99213",
            "decision_factors": ["History", "Examination", "MDM"]
        }
    }
    
    try:
        # Create request model - should work without timestamp
        request = UserFeedbackRequest(**test_data)
        print("✅ UserFeedbackRequest created successfully")
        print(f"   Request fields: {list(request.dict().keys())}")
        
        # Convert to entity - timestamp should be generated here
        entity = UserFeedbackEntity.from_request(request)
        print("✅ UserFeedbackEntity created successfully")
        print(f"   Entity has timestamp: {entity.user_action_timestamp}")
        
        # Convert to Azure entity
        azure_entity = entity.to_azure_entity()
        print("✅ Azure entity created successfully")
        print(f"   Azure entity has UserActionTimestamp: {'UserActionTimestamp' in azure_entity}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_rejected_feedback():
    """Test rejected feedback with reject_reason."""
    print("\nTesting rejected feedback...")
    
    test_data = {
        "suggested_em_code": "99214",
        "current_em_code": "99212", 
        "final_em_code": "99212",
        "user_action": "rejected",
        "reject_reason": "Documentation insufficient for higher level",
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "confidence_score": 0.75,
        "raw_agent_result": {
            "analysis": "Suggested 99214 but user disagreed",
            "decision_factors": ["History", "Examination", "MDM"]
        }
    }
    
    try:
        request = UserFeedbackRequest(**test_data)
        entity = UserFeedbackEntity.from_request(request)
        azure_entity = entity.to_azure_entity()
        
        print("✅ Rejected feedback processed successfully")
        print(f"   Reject reason: {azure_entity['RejectReason']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_validation_errors():
    """Test validation errors for missing required fields."""
    print("\nTesting validation errors...")
    
    # Test missing reject_reason when user_action is rejected
    invalid_data = {
        "suggested_em_code": "99214",
        "current_em_code": "99212", 
        "final_em_code": "99212",
        "user_action": "rejected",
        # Missing reject_reason
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "confidence_score": 0.75,
        "raw_agent_result": {"test": "data"}
    }
    
    try:
        request = UserFeedbackRequest(**invalid_data)
        print("❌ Should have failed validation")
        return False
        
    except Exception as e:
        print(f"✅ Validation error caught as expected: {e}")
        return True


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING FEEDBACK MODELS AFTER TIMESTAMP REMOVAL")
    print("=" * 60)
    
    test1 = test_feedback_request_without_timestamp()
    test2 = test_rejected_feedback()
    test3 = test_validation_errors()
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Request without timestamp: {'PASSED' if test1 else 'FAILED'}")
    print(f"Rejected feedback: {'PASSED' if test2 else 'FAILED'}")
    print(f"Validation errors: {'PASSED' if test3 else 'FAILED'}")
    
    if all([test1, test2, test3]):
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n❌ Some tests failed")
