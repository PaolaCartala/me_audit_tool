"""Test script for feedback endpoints."""

import json
import requests
from http import HTTPStatus

from constants import UserAction

# Test data - Accepted feedback
test_feedback_accepted = {
    "suggestedEmCode": "99213",
    "currentEmCode": "99212", 
    "finalEmCode": "99213",
    "userAction": UserAction.ACCEPTED.value,
    "rejectReason": None,
    "userId": "123e4567-e89b-12d3-a456-426614174000",
    "confidenceScore": 0.85,
    "rawAgentResult": {
        "analysis": "Patient meets criteria for 99213",
        "decision_factors": ["History", "Examination", "MDM"],
        "confidence": 0.85
    }
}

# Test data - Rejected feedback
test_feedback_rejected = {
    "suggestedEmCode": "99214",
    "currentEmCode": "99212", 
    "finalEmCode": "99212",
    "userAction": UserAction.REJECTED.value,
    "rejectReason": "Documentation insufficient for higher level",
    "userId": "123e4567-e89b-12d3-a456-426614174000",
    "confidenceScore": 0.75,
    "rawAgentResult": {
        "analysis": "Suggested 99214 but user disagreed",
        "decision_factors": ["History", "Examination", "MDM"],
        "confidence": 0.75
    }
}

def test_submit_feedback(base_url: str = "http://localhost:7071", test_data: dict = None):
    """Test the submit feedback endpoint."""
    if test_data is None:
        test_data = test_feedback_accepted
        
    print("Testing submit feedback endpoint...")
    
    url = f"{base_url}/api/feedback"
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=test_data, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == HTTPStatus.CREATED.value
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_analytics(base_url: str = "http://localhost:7071", test_data: dict = None):
    """Test the analytics endpoint."""
    if test_data is None:
        test_data = test_feedback_accepted
        
    print("Testing get analytics endpoint...")
    
    user_id = test_data["userId"]
    url = f"{base_url}/api/feedback/analytics?user_id={user_id}"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == HTTPStatus.OK.value
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Running feedback endpoint tests...")
    print("Make sure your Azure Function is running locally first!")
    print("Run: func start")
    print("-" * 50)
    
    # Test accepted feedback submission
    print("Testing ACCEPTED feedback:")
    submit_success_accepted = test_submit_feedback(test_data=test_feedback_accepted)
    print("-" * 50)
    
    # Test rejected feedback submission
    print("Testing REJECTED feedback:")
    submit_success_rejected = test_submit_feedback(test_data=test_feedback_rejected)
    print("-" * 50)
    
    # Test analytics retrieval 
    analytics_success = test_get_analytics()
    print("-" * 50)
    
    print(f"Submit accepted feedback test: {'PASSED' if submit_success_accepted else 'FAILED'}")
    print(f"Submit rejected feedback test: {'PASSED' if submit_success_rejected else 'FAILED'}")
    print(f"Analytics test: {'PASSED' if analytics_success else 'FAILED'}")
