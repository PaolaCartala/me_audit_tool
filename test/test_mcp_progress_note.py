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
from agents.em_progress_note_agent import main as em_progress_note_agent

# Load environment variables
load_dotenv()

# Define the test input data
test_input = "563543C8-23FF-481B-93DE-1D2C93959DE8"  # ID válido encontrado
# 175ac3cb-e718-40c7-805a-5306dcadee8a  # Este ID no existe en la BD


async def run_test():
    """
    Run the test for the Progress Note Generator Agent
    """
    start_time = time.time()
    logger.debug("Starting Progress Note Generator Agent test...")

    try:
        # Call the agent with the test input
        logger.debug(f"🚀 Llamando al agente con ID: {test_input}")
        result = await em_progress_note_agent(test_input)

        # Log the result
        logger.debug(f"✅ Test completado exitosamente!")
        logger.debug(f"⏱️ Tiempo transcurrido: {time.time() - start_time:.2f} segundos")
        logger.debug(f"📊 Tipo de resultado: {type(result)}")
        
        if isinstance(result, dict):
            logger.debug(f"📝 Claves en resultado: {list(result.keys())}")
            if 'progress_note' in result:
                note_length = len(result['progress_note']) if result['progress_note'] else 0
                logger.debug(f"📄 Longitud de progress note: {note_length} caracteres")
        
        # Save the result to a file
        output_file = Path("progress_note.json")
        with output_file.open("w") as f:
            json.dump(result, f, indent=4)
        logger.debug(f"💾 Resultado guardado en: {output_file}")

    except Exception as e:
        error_type = type(e).__name__
        logger.error(f"❌ Error durante el test: {error_type}: {e}")
        
        # Log más detalles del error
        import traceback
        logger.error(f"🔍 Traceback completo:")
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                logger.error(f"   {line}")
        
        # Crear reporte de error
        error_report = {
            "timestamp": datetime.now().isoformat(),
            "test_input": test_input,
            "error_type": error_type,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
        
        error_file = Path("progress_note_error.json")
        with error_file.open("w") as f:
            json.dump(error_report, f, indent=4)
        logger.error(f"📄 Reporte de error guardado en: {error_file}")

if __name__ == "__main__":
    # Run the test in an asyncio event loop
    asyncio.run(run_test())
    logger.debug("Test script completed.")
