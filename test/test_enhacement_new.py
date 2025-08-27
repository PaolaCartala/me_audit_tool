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
from agents.em_enhancement_agent import main as em_enhancement_agent

# Load environment variables
load_dotenv()

# Define the test input data
test_input = "175ac3cb-e718-40c7-805a-5306dcadee8a"
# 563543C8-23FF-481B-93DE-1D2C93959DE8


async def run_test():
    """
    Run the test for the Progress Note Generator Agent
    """
    start_time = time.time()
    logger.debug("Starting Progress Note Generator Agent test...")

    try:
        # Call the agent with the test input
        result = await em_enhancement_agent(test_input)

        # Log the result
        logger.debug(f"Result: {result}")
        logger.debug(f"Test completed successfully in {time.time() - start_time:.2f} seconds")
        
        # Save the result to a file
        output_file = Path("enhancement.json")
        with output_file.open("w") as f:
            json.dump(result, f, indent=4)
        logger.debug(f"Output saved to {output_file}")

    except Exception as e:
        logger.error(f"Error during test: {e}")

if __name__ == "__main__":
    # Run the test in an asyncio event loop
    asyncio.run(run_test())
    logger.debug("Test script completed.")
