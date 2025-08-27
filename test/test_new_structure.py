#!/usr/bin/env python3
"""
Test script to verify the new structured output format works correctly
"""
import asyncio
import json
from pydantic import ValidationError

from agents.models.pydantic_models import (
    CodeJustification, 
    ProviderFriendlyEvaluation, 
    EMCodeEvaluations,
    EMAuditResult,
    ConfidenceAssessment
)

async def test_structured_justification():
    """Test the new CodeJustification structure"""
    print("🧪 Testing CodeJustification structure...")
    
    # Test valid structure
    try:
        justification = CodeJustification(
            supportedBy="Supported by straightforward MDM per AMA 2025 E/M guidelines.",
            documentationSummary=[
                "One self-limited/minor problem",
                "Minimal/no reviewed or analyzed data",
                "Minimal risk"
            ],
            mdmConsiderations=[
                "No prescription medication, data analysis, or significant management decisions present",
                "No time recorded; MDM is sole driver for code selection"
            ],
            complianceAlerts=[
                "Higher codes would be considered upcoding based on documented MDM and risk level."
            ]
        )
        print("✅ CodeJustification validation passed!")
        print(f"📋 JSON output:\n{justification.model_dump_json(indent=2)}")
        
    except ValidationError as e:
        print(f"❌ CodeJustification validation failed: {e}")
        return False

    # Test without compliance alerts (optional field)
    try:
        justification_no_alerts = CodeJustification(
            supportedBy="Supported by moderate MDM per AMA 2025 E/M guidelines.",
            documentationSummary=[
                "Multiple chronic conditions managed",
                "Prescription medications reviewed and adjusted"
            ],
            mdmConsiderations=[
                "Active medication management present",
                "Multiple stable chronic conditions addressed"
            ]
        )
        print("✅ CodeJustification without compliance alerts passed!")
        
    except ValidationError as e:
        print(f"❌ CodeJustification without alerts failed: {e}")
        return False
    
    return True

async def test_provider_friendly_evaluation():
    """Test the new ProviderFriendlyEvaluation structure"""
    print("\n🧪 Testing ProviderFriendlyEvaluation structure...")
    
    try:
        evaluation = ProviderFriendlyEvaluation(
            mdmAssignmentReason=[
                "Single established patient with straightforward chronic condition management",
                "No new diagnostic tests ordered or complex data analysis required",
                "Minimal risk assessment with stable patient condition",
                "Standard follow-up care with no medication changes"
            ],
            documentationEnhancementOpportunities=[
                "Include more detail in physical examination findings",
                "Add functional assessment of patient's condition",
                "Document any patient education or counseling provided"
            ],
            scoring_impact="- -5 points: History/physical exam lacks specificity\n- -2 points: PMH contains unrelated issues not addressed",
            quick_tip="Even if a problem is unrelated, stating 'not addressed at this visit' can remove ambiguity."
        )
        print("✅ ProviderFriendlyEvaluation validation passed!")
        print(f"📋 JSON output:\n{evaluation.model_dump_json(indent=2)}")
        
    except ValidationError as e:
        print(f"❌ ProviderFriendlyEvaluation validation failed: {e}")
        return False
    
    return True

async def test_complete_audit_result():
    """Test the complete EMAuditResult with new structures"""
    print("\n🧪 Testing complete EMAuditResult structure...")
    
    try:
        # Create sample confidence assessment
        confidence = ConfidenceAssessment(
            score=85,
            tier="High",
            mdmAssignmentReason=["Clear documentation of moderate complexity medical decision making", "Appropriate risk assessment documented"],
            documentationEnhancementOpportunities=["Enhanced physical exam documentation", "More detailed risk assessment"],
            score_deductions=["- Score reduced by 15 points: Limited physical exam documentation"],
            quick_tip="Even if a problem is unrelated, stating 'not addressed at this visit' can remove ambiguity for coders and auditors."
        )
        
        # Create sample justification
        justification = CodeJustification(
            supportedBy="Supported by straightforward MDM per AMA 2025 E/M guidelines.",
            documentationSummary=[
                "One self-limited/minor problem",
                "Minimal/no reviewed or analyzed data",
                "Minimal risk"
            ],
            mdmConsiderations=[
                "No prescription medication present",
                "No time recorded; MDM is sole driver"
            ]
        )
        
        # Create sample evaluations
        evaluation_99212 = ProviderFriendlyEvaluation(
            mdmAssignmentReason=[
                "Straightforward MDM level clearly documented",
                "Single stable condition management"
            ],
            documentationEnhancementOpportunities=[
                "Add more exam details"
            ],
            scoring_impact="-5 points: Limited exam documentation"
        )
        
        evaluations = EMCodeEvaluations(
            code_99212_evaluation=evaluation_99212,
            code_99213_evaluation=evaluation_99212,  # Reusing for simplicity
            code_99214_evaluation=evaluation_99212,
            code_99215_evaluation=evaluation_99212
        )
        
        # Create complete audit result
        audit_result = EMAuditResult(
            audit_flags=["Documentation could be more detailed in physical exam section"],
            final_assigned_code="99212",
            final_justification=justification,
            code_evaluations=evaluations,
            billing_ready_note="Enhanced note with complete documentation...",
            confidence=confidence
        )
        
        print("✅ Complete EMAuditResult validation passed!")
        print(f"📋 Sample structure keys: {list(audit_result.model_dump().keys())}")
        
        # Verify the confidence structure has the correct fields
        result_dict = audit_result.model_dump()
        confidence_dict = result_dict['confidence']
        assert 'score' in confidence_dict
        assert 'tier' in confidence_dict
        assert 'mdmAssignmentReason' in confidence_dict
        assert 'documentationEnhancementOpportunities' in confidence_dict
        assert 'score_deductions' in confidence_dict
        assert 'quick_tip' in confidence_dict
        print("✅ New confidence assessment fields verified!")
        
        # Verify the evaluation structure has the new fields
        eval_99212 = result_dict['code_evaluations']['code_99212_evaluation']
        assert 'mdmAssignmentReason' in eval_99212
        assert 'documentationEnhancementOpportunities' in eval_99212
        assert 'scoring_impact' in eval_99212
        print("✅ New evaluation structure fields verified!")
        
    except ValidationError as e:
        print(f"❌ EMAuditResult validation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

async def main():
    """Run all tests"""
    print("🚀 Starting Enhanced Output Structure Tests\n")
    
    tests = [
        test_structured_justification(),
        test_provider_friendly_evaluation(),
        test_complete_audit_result()
    ]
    
    results = await asyncio.gather(*tests)
    
    if all(results):
        print("\n🎉 All tests passed! The new structured output format is working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Please check the output above.")
        return False

if __name__ == "__main__":
    asyncio.run(main())
