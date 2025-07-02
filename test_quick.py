"""
Quick Test Script for E/M Coding Agents
Tests with 2 sample PDFs to validate the setup
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from data.pdf_processor import PDFProcessor
from models.pydantic_models import EMInput, em_enhancement_agent, em_auditor_agent
from settings import logger

# Load environment variables
load_dotenv()


async def test_quick():
    """Quick test with 2 PDFs"""
    logger.info("🚀 Starting Quick E/M Coding Test")
    
    # Initialize PDF processor
    logger.debug("📁 Initializing PDF processor...")
    pdf_processor = PDFProcessor(use_form_recognizer=False)
    
    # Get sample directory
    sample_dir = Path("data/samples")
    if not sample_dir.exists():
        logger.error(f"❌ Sample directory not found: {sample_dir}")
        return
    
    # Process only 10 PDFs for quick test
    logger.debug("📄 Processing 10 sample PDFs...")
    em_inputs = pdf_processor.process_sample_pdfs(str(sample_dir), limit=10)
    
    if not em_inputs:
        logger.error("❌ No PDFs were successfully processed")
        return
    
    logger.debug(f"📊 Processing {len(em_inputs)} documents through agents...")
    
    # Process all available documents
    all_results = []
    
    for i, em_input in enumerate(em_inputs, 1):
        logger.info(f"\n� Processing document {i}/{len(em_inputs)}: {em_input.document_id}")
        logger.debug(f"📝 Text preview (first 300 chars): {em_input.text[:300]}...")
        
        try:
            # Stage 1: Enhancement Agent
            logger.info("🤖 Running Enhancement Agent...")
            
            enhancement_prompt = f"""
            Document ID: {em_input.document_id}
            Date of Service: {em_input.date_of_service}
            Provider: {em_input.provider}
            
            Progress Note:
            {em_input.text}
            
            Please analyze this progress note and assign the most appropriate E/M code with justifications.
            """
            
            logger.debug("🧠 Enhancement Agent: Processing...")
            enhancement_result = await em_enhancement_agent.run(enhancement_prompt)
            
            logger.debug("✅ Enhancement Agent completed!")
            logger.info(f"🎯 Assigned Code: {enhancement_result.output.assigned_code}")
            logger.info(f"📋 Justification: {enhancement_result.output.justification[:100]}...")
            
            logger.debug("📊 Code Recommendations:")
            logger.debug(f"  • 99212: {enhancement_result.output.code_recommendations.code_99212[:50]}...")
            logger.debug(f"  • 99213: {enhancement_result.output.code_recommendations.code_99213[:50]}...")
            logger.debug(f"  • 99214: {enhancement_result.output.code_recommendations.code_99214[:50]}...")
            logger.debug(f"  • 99215: {enhancement_result.output.code_recommendations.code_99215[:50]}...")
            
            # Stage 2: Auditor Agent
            logger.info("\n🕵️ Running Auditor Agent...")
            
            auditor_prompt = f"""
            Original Progress Note:
            {em_input.text}
            
            Enhancement Agent Results:
            - Assigned Code: {enhancement_result.output.assigned_code}
            - Justification: {enhancement_result.output.justification}
            - Code Recommendations:
              * 99212: {enhancement_result.output.code_recommendations.code_99212}
              * 99213: {enhancement_result.output.code_recommendations.code_99213}
              * 99214: {enhancement_result.output.code_recommendations.code_99214}
              * 99215: {enhancement_result.output.code_recommendations.code_99215}
            
            Please audit this analysis for compliance and provide final recommendations.
            """
            
            logger.debug("🧠 Auditor Agent: Processing...")
            auditor_result = await em_auditor_agent.run(auditor_prompt)
            
            logger.debug("✅ Auditor Agent completed!")
            logger.info(f"🎯 Final Code: {auditor_result.output.final_assigned_code}")
            logger.info(f"🚨 Audit Flags: {len(auditor_result.output.audit_flags)} flags")
            logger.info(f"� Final Justification: {auditor_result.output.final_justification[:100]}...")
            
            # Create JSON output for this document
            document_result = {
                "document_id": em_input.document_id,
                "date_of_service": em_input.date_of_service,
                "provider": em_input.provider,
                "original_text_length": len(em_input.text),
                "original_text_preview": em_input.text[:500] + "..." if len(em_input.text) > 500 else em_input.text,
                "enhancement_agent": {
                    "assigned_code": enhancement_result.output.assigned_code,
                    "justification": enhancement_result.output.justification,
                    "code_recommendations": {
                        "code_99212": enhancement_result.output.code_recommendations.code_99212,
                        "code_99213": enhancement_result.output.code_recommendations.code_99213,
                        "code_99214": enhancement_result.output.code_recommendations.code_99214,
                        "code_99215": enhancement_result.output.code_recommendations.code_99215,
                    }
                },
                "auditor_agent": {
                    "final_assigned_code": auditor_result.output.final_assigned_code,
                    "final_justification": auditor_result.output.final_justification,
                    "audit_flags": auditor_result.output.audit_flags,
                    "billing_ready_note": auditor_result.output.billing_ready_note,
                    "final_code_recommendations": {
                        "code_99212": auditor_result.output.final_code_recommendations.code_99212,
                        "code_99213": auditor_result.output.final_code_recommendations.code_99213,
                        "code_99214": auditor_result.output.final_code_recommendations.code_99214,
                        "code_99215": auditor_result.output.final_code_recommendations.code_99215,
                    }
                },
                "timestamp": datetime.now().isoformat(),
                "processing_metadata": {
                    "enhancement_agent_model": "Azure OpenAI GPT-4.1",
                    "auditor_agent_model": "Azure OpenAI GPT-4.1",
                    "processing_time": datetime.now().isoformat()
                }
            }
            
            # Save individual document result
            output_filename = f"result_{em_input.document_id}.json"
            with open(f'test_results/{output_filename}', "w", encoding="utf-8") as f:
                json.dump(document_result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Document result saved to: {output_filename}")
            
            # Add to consolidated results
            all_results.append(document_result)
            
            logger.debug(f"✅ Document {i}/{len(em_inputs)} completed successfully!")
            logger.debug("-" * 60)
            
        except Exception as e:
            logger.error(f"❌ Error processing document {em_input.document_id}: {str(e)}")
            import traceback
            logger.error(f"� Traceback: {traceback.format_exc()}")
            
            # Add error result
            error_result = {
                "document_id": em_input.document_id,
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
            all_results.append(error_result)
    
    # Save consolidated results
    consolidated_filename = f"test_results_consolidated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    consolidated_result = {
        "test_summary": {
            "total_documents": len(em_inputs),
            "successful_documents": len([r for r in all_results if "error" not in r]),
            "failed_documents": len([r for r in all_results if "error" in r]),
            "test_timestamp": datetime.now().isoformat(),
            "test_type": "quick_test_multiple_documents"
        },
        "results": all_results
    }
    
    with open(f'test_results/{consolidated_filename}', "w", encoding="utf-8") as f:
        json.dump(consolidated_result, f, indent=2, ensure_ascii=False)
    
    logger.debug(f"💾 Consolidated results saved to: {consolidated_filename}")
    
    # Print summary
    logger.debug("\n" + "="*80)
    logger.debug("📊 TEST SUMMARY")
    logger.debug("="*80)
    logger.debug(f"✅ Total documents processed: {len(em_inputs)}")
    logger.debug(f"✅ Successful: {consolidated_result['test_summary']['successful_documents']}")
    logger.debug(f"❌ Failed: {consolidated_result['test_summary']['failed_documents']}")
    
    # Show sample result structure
    if all_results and "error" not in all_results[0]:
        logger.debug("\n📄 SAMPLE RESULT STRUCTURE:")
        logger.debug("=" * 80)
        sample_result = all_results[0].copy()
        # Truncate long fields for display
        if "original_text_preview" in sample_result:
            sample_result["original_text_preview"] = sample_result["original_text_preview"][:200] + "..."
        for agent in ["enhancement_agent", "auditor_agent"]:
            if agent in sample_result:
                if "justification" in sample_result[agent]:
                    sample_result[agent]["justification"] = sample_result[agent]["justification"][:100] + "..."
                if "final_justification" in sample_result[agent]:
                    sample_result[agent]["final_justification"] = sample_result[agent]["final_justification"][:100] + "..."
                if "billing_ready_note" in sample_result[agent]:
                    sample_result[agent]["billing_ready_note"] = sample_result[agent]["billing_ready_note"][:100] + "..."
                if "code_recommendations" in sample_result[agent]:
                    for code in sample_result[agent]["code_recommendations"]:
                        sample_result[agent]["code_recommendations"][code] = sample_result[agent]["code_recommendations"][code][:50] + "..."
                if "final_code_recommendations" in sample_result[agent]:
                    for code in sample_result[agent]["final_code_recommendations"]:
                        sample_result[agent]["final_code_recommendations"][code] = sample_result[agent]["final_code_recommendations"][code][:50] + "..."
        
        logger.debug(json.dumps(sample_result, indent=2, ensure_ascii=False))
        logger.debug("=" * 80)
    
    logger.info("🎉 Test completed successfully!")


def main():
    """Main entry point"""
    try:
        asyncio.run(test_quick())
    except KeyboardInterrupt:
        logger.info("⏹️ Test interrupted by user")
    except Exception as e:
        logger.error(f"💥 Test failed with error: {str(e)}")


if __name__ == "__main__":
    main()
