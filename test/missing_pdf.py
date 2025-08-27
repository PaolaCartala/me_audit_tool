"""
Compare PDFs in data/35_test with JSON results to find missing ones
"""
import os
from pathlib import Path
from settings import logger

def compare_pdfs_and_jsons():
    """Compare PDF files with JSON results to find missing ones"""
    
    # Define directories
    pdf_dir = Path("data/35_test")
    # json_dir = Path("data/completed/35_test/test_results_jsons_new")
    json_dir = Path("test_results")
    
    # Check if directories exist
    if not pdf_dir.exists():
        logger.error(f"❌ PDF directory not found: {pdf_dir}")
        return
    
    if not json_dir.exists():
        logger.error(f"❌ JSON directory not found: {json_dir}")
        return
    
    # Get all PDF files
    pdf_files = list(pdf_dir.glob("*.pdf"))
    pdf_names = {pdf.stem for pdf in pdf_files}  # Get names without .pdf extension
    
    logger.debug(f"📄 Found {len(pdf_files)} PDF files in {pdf_dir}")
    
    # Get all JSON result files (those starting with "result_")
    json_files = list(json_dir.glob("result_*.json"))
    
    # Extract document IDs from JSON filenames
    # JSON files are named like "result_DOCUMENT_ID.json"
    json_document_ids = set()
    for json_file in json_files:
        filename = json_file.stem  # Remove .json extension
        if filename.startswith("result_"):
            document_id = filename[7:]  # Remove "result_" prefix
            json_document_ids.add(document_id)
    
    logger.debug(f"📊 Found {len(json_files)} JSON result files in {json_dir}")
    logger.debug(f"📊 Extracted {len(json_document_ids)} document IDs from JSON files")
    
    # Find PDFs without corresponding JSON results
    missing_jsons = pdf_names - json_document_ids
    
    # Find JSON results without corresponding PDFs (shouldn't happen but good to check)
    extra_jsons = json_document_ids - pdf_names
    
    # Print results
    logger.debug("\n" + "="*60)
    logger.debug("📊 COMPARISON RESULTS")
    logger.debug("="*60)
    
    if missing_jsons:
        logger.warning(f"❌ Found {len(missing_jsons)} PDF(s) without JSON results:")
        for pdf_name in sorted(missing_jsons):
            logger.warning(f"   • {pdf_name}.pdf")
            
        # Show the full path for easy verification
        logger.debug("\n📁 Full paths of missing results:")
        for pdf_name in sorted(missing_jsons):
            pdf_path = pdf_dir / f"{pdf_name}.pdf"
            expected_json_path = json_dir / f"result_{pdf_name}.json"
            logger.debug(f"   📄 PDF: {pdf_path}")
            logger.debug(f"   ❌ Expected JSON: {expected_json_path}")
            logger.debug("")
    else:
        logger.debug("✅ All PDFs have corresponding JSON results!")
    
    if extra_jsons:
        logger.warning(f"⚠️ Found {len(extra_jsons)} JSON result(s) without corresponding PDFs:")
        for json_name in sorted(extra_jsons):
            logger.warning(f"   • result_{json_name}.json")
    else:
        logger.debug("✅ All JSON results have corresponding PDFs!")
    
    # Summary
    logger.debug(f"\n📈 SUMMARY:")
    logger.debug(f"   📄 Total PDFs: {len(pdf_files)}")
    logger.debug(f"   📊 Total JSON results: {len(json_files)}")
    logger.debug(f"   ❌ Missing JSON results: {len(missing_jsons)}")
    logger.debug(f"   ⚠️ Extra JSON results: {len(extra_jsons)}")
    
    return missing_jsons, extra_jsons

def main():
    """Main entry point"""
    try:
        missing, extra = compare_pdfs_and_jsons()
        
        if missing:
            logger.debug(f"\n🎯 ACTION NEEDED: Process these {len(missing)} PDF(s):")
            for pdf_name in sorted(missing):
                logger.debug(f"   • {pdf_name}.pdf")
    
    except Exception as e:
        logger.error(f"💥 Comparison failed with error: {str(e)}")
        import traceback
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()