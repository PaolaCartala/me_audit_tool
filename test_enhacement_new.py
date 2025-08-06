"""
Quick Test Script for Progress Note Generator Agent
"""
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from settings import logger
from subagents.em_enhancement_agent import main as em_enhancement_agent
# Load environment variables
load_dotenv()
# Define the test input data
test_input = "175ac3cb-e718-40c7-805a-5306dcadee8a"
async def run_test():
    """
    Run the test for the Progress Note Generator Agent
    """
    start_time = time.time()
    logger.info("Starting Progress Note Generator Agent test...")

    try:
        # Call the agent with the test input
        result = await em_enhancement_agent(test_input)

        # Log the result
        logger.info(f"Result: {result}")
        logger.info(f"Test completed successfully in {time.time() - start_time:.2f} seconds")
        
        # Save the result to a file
        output_file = Path("enhancement.json")
        with output_file.open("w") as f:
            json.dump(result, f, indent=4)
        logger.info(f"Output saved to {output_file}")

    except Exception as e:
        logger.error(f"Error during test: {e}")
if __name__ == "__main__":
    # Run the test in an asyncio event loop
    asyncio.run(run_test())
    logger.info("Test script completed.")