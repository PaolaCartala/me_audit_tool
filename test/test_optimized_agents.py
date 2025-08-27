#!/usr/bin/env python3
"""
Script de prueba rápida para agentes optimizados
Ejecuta: python test_optimized_agents.py
"""
import asyncio
import time
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from settings import logger

# Test the optimized models import
try:
    from agents.models.optimized_pydantic_models import (
        get_optimized_em_enhancement_agent,
        get_optimized_em_auditor_agent,
        OptimizedEMInput
    )
    print("✅ Optimized models imported successfully")
except Exception as e:
    print(f"❌ Error importing optimized models: {e}")
    sys.exit(1)


async def test_optimized_enhancement_direct(test_text: str) -> dict:
    """Test optimized enhancement agent directly with text"""
    start_time = time.perf_counter()
    
    logger.debug("🚀 Testing Optimized Enhancement Agent")
    
    try:
        # Get the optimized agent
        agent = get_optimized_em_enhancement_agent()
        
        # Create minimal prompt
        prompt = f"""Medical Note:
{test_text}

Analyze and assign appropriate E/M code (99212-99215) with brief MDM-focused justification."""
        
        # Run agent
        result = await agent.run(prompt)
        
        total_time = time.perf_counter() - start_time
        
        return {
            "success": True,
            "assigned_code": result.output.assigned_code,
            "justification": result.output.justification,
            "execution_time": round(total_time, 2),
        }
        
    except Exception as e:
        total_time = time.perf_counter() - start_time
        logger.error(f"❌ Enhancement agent test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "execution_time": round(total_time, 2),
        }


async def test_optimized_auditor_direct(enhancement_result: dict) -> dict:
    """Test optimized auditor agent directly"""
    start_time = time.perf_counter()
    
    logger.debug("🚀 Testing Optimized Auditor Agent")
    
    try:
        # Get the optimized agent
        agent = get_optimized_em_auditor_agent()
        
        # Create focused audit prompt
        prompt = f"""AUDIT REQUEST
Enhancement Agent Result:
- Assigned Code: {enhancement_result.get('assigned_code')}
- Justification: {enhancement_result.get('justification')}

TASK: Review the enhancement agent's code assignment and provide:
1. Audit flags for compliance risks
2. Final code assignment (confirm or adjust)
3. Structured justification with MDM breakdown
4. Confidence assessment with specific score deductions"""
        
        # Run agent
        result = await agent.run(prompt)
        
        total_time = time.perf_counter() - start_time
        
        return {
            "success": True,
            "audit_flags": result.output.audit_flags,
            "final_assigned_code": result.output.final_assigned_code,
            "final_justification": result.output.final_justification,
            "confidence": result.output.confidence,
            "execution_time": round(total_time, 2),
        }
        
    except Exception as e:
        total_time = time.perf_counter() - start_time
        logger.error(f"❌ Auditor agent test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "execution_time": round(total_time, 2),
        }


async def run_optimized_pipeline_test():
    """Run complete optimized pipeline test"""
    print("🎯 Starting Optimized Pipeline Test")
    pipeline_start = time.perf_counter()
    
    # Sample medical note for testing
    test_medical_note = """
SUBJECTIVE:
Patient presents with worsening low back pain radiating to left leg for 3 weeks. 
Pain is 7/10, worse with sitting and bending. No bowel/bladder dysfunction.
Patient has tried ibuprofen with minimal relief.

OBJECTIVE:
Vital signs stable. Neurological exam shows decreased sensation L5 distribution.
Straight leg raise positive on left at 45 degrees. Deep tendon reflexes intact.

ASSESSMENT & PLAN:
Lumbar radiculopathy likely L5 nerve root. 
1. Ordered MRI lumbar spine
2. Prescribed gabapentin 300mg TID
3. Physical therapy referral
4. Follow up in 2 weeks or sooner if symptoms worsen
"""
    
    try:
        # Step 1: Test Enhancement Agent
        print("📋 Step 1: Testing Enhancement Agent...")
        enhancement_result = await test_optimized_enhancement_direct(test_medical_note)
        
        if not enhancement_result["success"]:
            print(f"❌ Enhancement failed: {enhancement_result['error']}")
            return
            
        print(f"✅ Enhancement completed in {enhancement_result['execution_time']}s")
        print(f"   Assigned Code: {enhancement_result['assigned_code']}")
        print(f"   Justification: {enhancement_result['justification'][:100]}...")
        
        # Step 2: Test Auditor Agent
        print("\n🔍 Step 2: Testing Auditor Agent...")
        auditor_result = await test_optimized_auditor_direct(enhancement_result)
        
        if not auditor_result["success"]:
            print(f"❌ Auditor failed: {auditor_result['error']}")
            return
            
        print(f"✅ Audit completed in {auditor_result['execution_time']}s")
        print(f"   Final Code: {auditor_result['final_assigned_code']}")
        print(f"   Confidence Score: {auditor_result['confidence']['score']}")
        print(f"   Confidence Tier: {auditor_result['confidence']['tier']}")
        print(f"   Audit Flags: {len(auditor_result['audit_flags'])} flags")
        
        # Calculate total performance
        total_pipeline_time = time.perf_counter() - pipeline_start
        
        print(f"\n🏆 Pipeline Performance Summary:")
        print(f"   Enhancement Time: {enhancement_result['execution_time']}s")
        print(f"   Auditor Time: {auditor_result['execution_time']}s")
        print(f"   Total Pipeline Time: {round(total_pipeline_time, 2)}s")
        print(f"   AI Processing Time: {enhancement_result['execution_time'] + auditor_result['execution_time']}s")
        
        # Success message
        print(f"\n🎉 Optimized Pipeline Test SUCCESSFUL!")
        print(f"   Both agents working with optimized prompts and aggressive timeouts")
        print(f"   No guidelines_cache dependency - direct prompt integration")
        
        return {
            "success": True,
            "enhancement_result": enhancement_result,
            "auditor_result": auditor_result,
            "total_pipeline_time": round(total_pipeline_time, 2)
        }
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        logger.error(f"Pipeline test error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    print("🚀 Optimized Agents Performance Test")
    print("=" * 50)
    
    # Run the test
    result = asyncio.run(run_optimized_pipeline_test())
    
    if result and result.get("success"):
        print(f"\n✅ TEST PASSED - Optimizations Working!")
    else:
        print(f"\n❌ TEST FAILED")
        sys.exit(1)
