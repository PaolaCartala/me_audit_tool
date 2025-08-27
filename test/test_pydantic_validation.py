"""Test script for Pydantic model validation."""

from datetime import datetime
from pydantic import ValidationError

from agents.models.feedback_models import UserFeedbackRequest
from constants import UserAction


def test_valid_accepted_feedback():
    """Test valid accepted feedback."""
    print("Testing valid ACCEPTED feedback...")
    
    try:
        feedback = UserFeedbackRequest(
            suggested_em_code="99213",
            current_em_code="99212",
            final_em_code="99213",
            user_action=UserAction.ACCEPTED.value,
            # user_action_timestamp will be auto-generated
            reject_reason=None,  # Should be fine for accepted
            user_id="123e4567-e89b-12d3-a456-426614174000",
            confidence_score=0.85,
            raw_agent_result={"test": "data"}
        )
        print("✅ Valid accepted feedback created successfully")
        print(f"   Auto-generated timestamp: {feedback.user_action_timestamp}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_valid_rejected_feedback():
    """Test valid rejected feedback."""
    print("Testing valid REJECTED feedback...")
    
    try:
        feedback = UserFeedbackRequest(
            suggested_em_code="99214",
            current_em_code="99212",
            final_em_code="99212",
            user_action=UserAction.REJECTED.value,
            # user_action_timestamp will be auto-generated
            reject_reason="Documentation insufficient",  # Required for rejected
            user_id="123e4567-e89b-12d3-a456-426614174000",
            confidence_score=0.75,
            raw_agent_result={"test": "data"}
        )
        print("✅ Valid rejected feedback created successfully")
        print(f"   Auto-generated timestamp: {feedback.user_action_timestamp}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_invalid_user_action():
    """Test invalid user action."""
    print("Testing invalid user_action...")
    
    try:
        feedback = UserFeedbackRequest(
            suggested_em_code="99213",
            current_em_code="99212",
            final_em_code="99213",
            user_action="invalid_action",  # Should fail validation
            # user_action_timestamp will be auto-generated
            reject_reason=None,
            user_id="123e4567-e89b-12d3-a456-426614174000",
            confidence_score=0.85,
            raw_agent_result={"test": "data"}
        )
        print("❌ Should have failed validation!")
        return False
    except ValidationError as e:
        print("✅ Validation error caught as expected:")
        print(f"   {e}")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_missing_reject_reason():
    """Test rejected feedback without reject_reason."""
    print("Testing rejected feedback without reject_reason...")
    
    try:
        feedback = UserFeedbackRequest(
            suggested_em_code="99214",
            current_em_code="99212",
            final_em_code="99212",
            user_action=UserAction.REJECTED.value,
            # user_action_timestamp will be auto-generated
            reject_reason=None,  # Should fail for rejected action
            user_id="123e4567-e89b-12d3-a456-426614174000",
            confidence_score=0.75,
            raw_agent_result={"test": "data"}
        )
        print("❌ Should have failed validation!")
        return False
    except ValidationError as e:
        print("✅ Validation error caught as expected:")
        print(f"   {e}")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_invalid_confidence_score():
    """Test invalid confidence score."""
    print("Testing invalid confidence_score (out of range)...")
    
    try:
        feedback = UserFeedbackRequest(
            suggested_em_code="99213",
            current_em_code="99212",
            final_em_code="99213",
            user_action=UserAction.ACCEPTED.value,
            # user_action_timestamp will be auto-generated
            reject_reason=None,
            user_id="123e4567-e89b-12d3-a456-426614174000",
            confidence_score=1.5,  # Should fail (> 1.0)
            raw_agent_result={"test": "data"}
        )
        print("❌ Should have failed validation!")
        return False
    except ValidationError as e:
        print("✅ Validation error caught as expected:")
        print(f"   {e}")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    print("Running Pydantic model validation tests...")
    print("=" * 50)
    
    tests = [
        test_valid_accepted_feedback,
        test_valid_rejected_feedback,
        test_invalid_user_action,
        test_missing_reject_reason,
        test_invalid_confidence_score
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        print("-" * 40)
    
    print(f"\nTest Results: {sum(results)}/{len(results)} passed")
    if all(results):
        print("🎉 All validation tests passed!")
    else:
        print("⚠️ Some tests failed.")
