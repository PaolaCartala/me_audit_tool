#!/usr/bin/env python3
"""
Setup script for E/M Evaluator project
Configures the environment and validates dependencies
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 9):
        logger.error("Python 3.9 or higher is required")
        sys.exit(1)
    logger.info(f"Python version check passed: {sys.version}")


def install_dependencies():
    """Install required dependencies"""
    logger.info("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        logger.info("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        sys.exit(1)


def check_azure_config():
    """Check Azure OpenAI configuration"""
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY", 
        "AZURE_OPENAI_DEPLOYMENT_NAME"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing Azure OpenAI configuration: {', '.join(missing_vars)}")
        logger.info("Please update local.settings.json with your Azure OpenAI credentials")
        return False
    
    logger.info("Azure OpenAI configuration found")
    return True


def validate_sample_data():
    """Check if sample PDF data is available"""
    sample_dir = Path("data/samples")
    if not sample_dir.exists():
        logger.warning(f"Sample data directory not found: {sample_dir}")
        return False
    
    pdf_files = list(sample_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning("No PDF files found in sample directory")
        return False
    
    logger.info(f"Found {len(pdf_files)} sample PDF files")
    return True


def run_basic_tests():
    """Run basic functionality tests"""
    logger.info("Running basic tests...")
    
    try:
        # Test imports
        from models.pydantic_models import EMInput, em_enhancement_agent, em_auditor_agent
        from data.pdf_processor import PDFProcessor
        logger.info("✓ Core modules import successfully")
        
        # Test PDF processor
        processor = PDFProcessor(use_form_recognizer=False)
        logger.info("✓ PDF processor initialized")
        
        # Test sample data processing (if available)
        if validate_sample_data():
            sample_inputs = processor.process_sample_pdfs("data/samples", limit=1)
            if sample_inputs:
                logger.info("✓ Sample PDF processing works")
            else:
                logger.warning("⚠ Sample PDF processing returned no results")
        
        logger.info("Basic tests completed successfully")
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"Test error: {e}")
        return False
    
    return True


def create_env_file():
    """Create a .env file template"""
    env_content = """# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-azure-openai-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-10-21

# Optional: Azure Form Recognizer (for advanced PDF processing)
AZURE_FORM_RECOGNIZER_ENDPOINT=https://your-form-recognizer.cognitiveservices.azure.com/
AZURE_FORM_RECOGNIZER_KEY=your-form-recognizer-key

# Azure Functions Configuration
AzureWebJobsStorage=DefaultEndpointsProtocol=https;AccountName=your-storage;AccountKey=your-key;EndpointSuffix=core.windows.net
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write(env_content)
        logger.info("Created .env template file - please update with your credentials")
    else:
        logger.info(".env file already exists")


def main():
    """Main setup function"""
    logger.info("Starting E/M Evaluator setup...")
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    install_dependencies()
    
    # Create environment file template
    create_env_file()
    
    # Check configuration
    azure_configured = check_azure_config()
    sample_data_available = validate_sample_data()
    
    # Run basic tests
    tests_passed = run_basic_tests()
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("SETUP SUMMARY")
    logger.info("="*50)
    logger.info(f"✓ Python version: {sys.version_info.major}.{sys.version_info.minor}")
    logger.info(f"✓ Dependencies: Installed")
    logger.info(f"{'✓' if azure_configured else '⚠'} Azure OpenAI: {'Configured' if azure_configured else 'Needs configuration'}")
    logger.info(f"{'✓' if sample_data_available else '⚠'} Sample data: {'Available' if sample_data_available else 'Not found'}")
    logger.info(f"{'✓' if tests_passed else '✗'} Basic tests: {'Passed' if tests_passed else 'Failed'}")
    
    if not azure_configured:
        logger.info("\nNext steps:")
        logger.info("1. Update local.settings.json with your Azure OpenAI credentials")
        logger.info("2. Run 'func start' to start the Azure Functions runtime")
        logger.info("3. Test the endpoints using the /test_samples endpoint")
    else:
        logger.info("\nSetup complete! You can now:")
        logger.info("1. Run 'func start' to start the Azure Functions runtime")
        logger.info("2. Test with: curl http://localhost:7071/api/test_samples")


if __name__ == "__main__":
    main()
