"""
Script de prueba de latencia para el Enhancement Agent
"""
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from settings import logger
from agents.em_enhancement_agent import main as em_enhancement_agent

# Load environment variables
load_dotenv()

# Define the test input data
test_document_id = "175ac3cb-e718-40c7-805a-5306dcadee8a"


async def run_latency_test():
    """
    Run the latency test for the Enhancement Agent
    """
    start_time = time.time()
    logger.debug("🧪 Starting Enhanced Enhancement Agent Latency Test...")
    logger.debug(f"📋 Test Document ID: {test_document_id}")

    try:
        # Call the agent with the test input
        result = await em_enhancement_agent(test_document_id)

        # Log the result with performance data
        total_test_time = time.time() - start_time
        
        # Extract performance metrics if available
        performance_metrics = result.get('performance_metrics', {})
        
        logger.debug("🎯 LATENCY TEST RESULTS SUMMARY:")
        logger.debug(f"📊 Total Test Time: {total_test_time:.2f} seconds")
        
        if performance_metrics:
            breakdown = performance_metrics.get('breakdown', {})
            logger.debug(f"🤖 AI Inference Time: {breakdown.get('ai_inference_time', 'N/A'):.2f}s")
            logger.debug(f"📡 MCP Operations Time: {breakdown.get('mcp_operations_time', 'N/A'):.2f}s") 
            logger.debug(f"⚙️ Data Processing Time: {breakdown.get('data_processing_time', 'N/A'):.2f}s")
            logger.debug(f"🔧 Agent Init Time: {breakdown.get('agent_init_time', 'N/A'):.2f}s")
            
            bottleneck_analysis = performance_metrics.get('bottleneck_analysis', {})
            primary_bottleneck = bottleneck_analysis.get('primary_bottleneck', 'unknown')
            logger.debug(f"🚨 Primary Bottleneck: {primary_bottleneck}")
            
            # recommendations = bottleneck_analysis.get('optimization_recommendations', [])
            # if recommendations:
            #     logger.debug("💡 Optimization Recommendations:")
            #     for rec in recommendations:
            #         if rec:
            #             logger.debug(f"  • {rec}")
        
        # Log final assignment
        assigned_code = result.get('assigned_code', 'N/A')
        logger.debug(f"🎯 Assigned E/M Code: {assigned_code}")
        
        # Save the result to a file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(f"latency_test_result_{timestamp}.json")
        with output_file.open("w") as f:
            json.dump(result, f, indent=4)
        logger.debug(f"💾 Output saved to {output_file}")

    except Exception as e:
        logger.error(f"❌ Error during latency test: {e}", exc_info=True)


if __name__ == "__main__":
    # Run the test in an asyncio event loop
    asyncio.run(run_latency_test())
    logger.debug("🏁 Latency test completed.")
