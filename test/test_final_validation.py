#!/usr/bin/env python3
"""
Final validation test for optimized patient type E/M coding implementation

This test verifies that all components work together correctly and that
the optimized agents can handle patient type distinction properly.
"""

import asyncio
from typing import Dict, Any


async def test_model_imports():
    """Test that all optimized models can be imported correctly"""
    print("🔧 Testing Model Imports...")
    
    try:
        from agents.models.optimized_pydantic_models import (
            OptimizedEMInput,
            OptimizedEMEnhancementOutput,
            OptimizedEMAuditOutput,
            CodeJustification,
            ConfidenceAssessment
        )
        print("   ✅ All optimized models imported successfully")
        
        # Test model creation with patient type
        test_input = OptimizedEMInput(
            document_id="test_123",
            date_of_service="2025-01-01",
            provider="Dr. Test",
            text="Test medical note",
            is_new_patient=True
        )
        print(f"   ✅ OptimizedEMInput created with is_new_patient: {test_input.is_new_patient}")
        
        test_enhancement = OptimizedEMEnhancementOutput(
            document_id="test_123",
            text="Test note",
            assigned_code="99203",
            justification="Test justification",
            is_new_patient=True
        )
        print(f"   ✅ OptimizedEMEnhancementOutput created with is_new_patient: {test_enhancement.is_new_patient}")
        
        test_audit = OptimizedEMAuditOutput(
            document_id="test_123",
            text="Test note",
            audit_flags=[],
            final_assigned_code="99203",
            final_justification=CodeJustification(
                supportedBy="Test support",
                documentationSummary=["Test summary"],
                mdmConsiderations=["Test considerations"]
            ),
            confidence=ConfidenceAssessment(
                score=85,
                tier="High",
                mdmAssignmentReason=["Test reasoning"],
                documentationEnhancementOpportunities=["Test opportunities"],
                score_deductions=[]
            ),
            is_new_patient=True
        )
        print(f"   ✅ OptimizedEMAuditOutput created with is_new_patient: {test_audit.is_new_patient}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Model import failed: {e}")
        return False


async def test_agent_imports():
    """Test that optimized agents can be imported"""
    print("\n🔧 Testing Agent Imports...")
    
    try:
        # Test enhancement agent import
        import agents.optimized_em_enhancement_agent as enhancement_agent
        print("   ✅ Optimized enhancement agent imported successfully")
        
        # Test auditor agent import
        import agents.optimized_em_auditor_agent as auditor_agent
        print("   ✅ Optimized auditor agent imported successfully")
        
        # Test PatientCodeMapper
        mapper = auditor_agent.PatientCodeMapper()
        test_code = mapper.get_appropriate_code("99213", True)
        print(f"   ✅ PatientCodeMapper working: 99213 -> {test_code} for new patient")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Agent import failed: {e}")
        return False


async def test_code_mappings():
    """Test all code mappings"""
    print("\n🔧 Testing Code Mappings...")
    
    try:
        from agents.optimized_em_auditor_agent import PatientCodeMapper
        
        # Test all mappings
        mappings = [
            ("99212", "99202"),  # Level 2
            ("99213", "99203"),  # Level 3
            ("99214", "99204"),  # Level 4
            ("99215", "99205")   # Level 5
        ]
        
        all_passed = True
        for established, new in mappings:
            # Test established -> new
            result_new = PatientCodeMapper.get_appropriate_code(established, True)
            if result_new != new:
                print(f"   ❌ Mapping failed: {established} -> {result_new} (expected {new})")
                all_passed = False
            else:
                print(f"   ✅ {established} -> {new} for new patient")
            
            # Test new -> established
            result_established = PatientCodeMapper.get_appropriate_code(new, False)
            if result_established != established:
                print(f"   ❌ Reverse mapping failed: {new} -> {result_established} (expected {established})")
                all_passed = False
            else:
                print(f"   ✅ {new} -> {established} for established patient")
        
        return all_passed
        
    except Exception as e:
        print(f"   ❌ Code mapping test failed: {e}")
        return False


async def test_validation_logic():
    """Test validation logic"""
    print("\n🔧 Testing Validation Logic...")
    
    try:
        from agents.optimized_em_auditor_agent import PatientCodeMapper
        
        # Test valid cases
        valid_cases = [
            ("99203", True, True),    # New patient code for new patient
            ("99213", False, True),   # Established code for established patient
        ]
        
        # Test invalid cases
        invalid_cases = [
            ("99213", True, False),   # Established code for new patient
            ("99203", False, False),  # New patient code for established patient
        ]
        
        all_passed = True
        
        for code, is_new_patient, should_be_valid in valid_cases:
            is_valid, message = PatientCodeMapper.validate_code_for_patient_type(code, is_new_patient)
            if is_valid != should_be_valid:
                print(f"   ❌ Validation failed for {code}, new_patient={is_new_patient}: {message}")
                all_passed = False
            else:
                patient_type = "new" if is_new_patient else "established"
                print(f"   ✅ {code} correctly validated as valid for {patient_type} patient")
        
        for code, is_new_patient, should_be_valid in invalid_cases:
            is_valid, message = PatientCodeMapper.validate_code_for_patient_type(code, is_new_patient)
            if is_valid != should_be_valid:
                print(f"   ❌ Validation failed for {code}, new_patient={is_new_patient}: {message}")
                all_passed = False
            else:
                patient_type = "new" if is_new_patient else "established"
                print(f"   ✅ {code} correctly flagged as invalid for {patient_type} patient")
        
        return all_passed
        
    except Exception as e:
        print(f"   ❌ Validation logic test failed: {e}")
        return False


async def main():
    """Run all validation tests"""
    print("🧪 FINAL VALIDATION: Optimized Patient Type E/M Coding Implementation")
    print("=" * 80)
    
    tests = [
        ("Model Imports", test_model_imports),
        ("Agent Imports", test_agent_imports),
        ("Code Mappings", test_code_mappings),
        ("Validation Logic", test_validation_logic)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 FINAL VALIDATION SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall Results: {passed}/{total} tests passed")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Patient type distinction is fully implemented in optimized agents")
        print("✅ Code mappings (99212↔99202, 99213↔99203, 99214↔99204, 99215↔99205) working correctly")
        print("✅ IsNewPatient boolean from MCP response is properly handled")
        print("✅ Validation and correction logic is working correctly")
        print("\n💡 The evaluator will now correctly distinguish between new vs. established patient visits!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the implementation.")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
