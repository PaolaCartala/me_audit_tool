"""
Guidelines Cache Module
Provides in-memory caching for E/M coding guidelines to improve performance
"""
import os
import asyncio
from pathlib import Path
from typing import Optional
from functools import lru_cache
import threading

from settings import logger


class GuidelinesCache:
    """Thread-safe singleton cache for E/M coding guidelines"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not getattr(self, '_initialized', False):
            self._em_guidelines_cache = None
            self._pdf_guidelines_cache = None
            self._guidelines_dir = Path(__file__).parent.parent / "guidelines"
            self._cache_lock = threading.RLock()
            self._initialized = True
            self._cache_warming = False
    
    async def warm_cache_async(self):
        """Asynchronously warm the cache in background"""
        if self._cache_warming or self._em_guidelines_cache is not None:
            return
            
        self._cache_warming = True
        try:
            logger.info("Starting asynchronous guidelines cache warming...")
            # Run cache warming in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.get_em_guidelines)
            logger.info("Asynchronous guidelines cache warming completed")
        except Exception as e:
            logger.error(f"Error during asynchronous cache warming: {str(e)}")
        finally:
            self._cache_warming = False
    
    def _load_markdown_guidelines(self) -> str:
        """Load markdown guidelines from file"""
        md_file = self._guidelines_dir / "em_guideline.md"
        if md_file.exists():
            with open(md_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def _load_pdf_guidelines(self) -> str:
        """Load PDF guidelines from file"""
        try:
            from utils.pdf_processor import PDFProcessor
            pdf_file = self._guidelines_dir / "ama_em_guideline.pdf"
            if pdf_file.exists():
                processor = PDFProcessor()
                return processor.extract_text(str(pdf_file))
        except ImportError:
            logger.warning("PDFProcessor not available. Skipping PDF guidelines.")
        except Exception as e:
            logger.error(f"Error loading PDF guidelines: {str(e)}")
        return ""
    
    def get_em_guidelines(self) -> str:
        """Get cached E/M coding guidelines"""
        with self._cache_lock:
            if self._em_guidelines_cache is None:
                logger.info("Loading E/M guidelines into cache...")
                md_content = self._load_markdown_guidelines()
                pdf_content = self._load_pdf_guidelines()
                
                guidelines_content = md_content
                if pdf_content.strip():
                    guidelines_content += "\n\n=== AMA E/M GUIDELINES PDF CONTENT ===\n\n" + pdf_content
                
                if not guidelines_content.strip():
                    guidelines_content = "Guidelines not found. Please ensure guidelines files are available in the guidelines/ directory."
                
                self._em_guidelines_cache = guidelines_content
                logger.info(f"E/M guidelines cached successfully ({len(guidelines_content)} characters)")
            
            return self._em_guidelines_cache
    
    def get_specific_code_requirements(self, code: str) -> str:
        """Get cached specific requirements for a particular E/M code"""
        guidelines = self.get_em_guidelines()
        
        # Use LRU cache for parsed code requirements
        return self._extract_code_requirements(guidelines, code)
    
    @lru_cache(maxsize=10)
    def _extract_code_requirements(self, guidelines: str, code: str) -> str:
        """Extract and cache specific code requirements"""
        code_sections = {
            "99212": "CPT Code 99212",
            "99213": "CPT Code 99213", 
            "99214": "CPT Code 99214",
            "99215": "CPT Code 99215"
        }
        
        if code not in code_sections:
            return f"Invalid code '{code}'. Valid codes are: 99212, 99213, 99214, 99215"
        
        # Find the specific section in guidelines
        lines = guidelines.split('\n')
        code_content = []
        in_code_section = False
        
        for line in lines:
            if code_sections[code] in line:
                in_code_section = True
            elif in_code_section and any(other_code in line for other_code in code_sections.values() if other_code != code_sections[code]):
                break
            
            if in_code_section:
                code_content.append(line)
        
        if code_content:
            return '\n'.join(code_content)
        else:
            return f"Specific requirements for {code} not found in guidelines."
    
    def get_mdm_complexity_guide(self) -> str:
        """Get cached MDM complexity guidelines"""
        guidelines = self.get_em_guidelines()
        return self._extract_mdm_content(guidelines)
    
    @lru_cache(maxsize=1)
    def _extract_mdm_content(self, guidelines: str) -> str:
        """Extract and cache MDM-related content"""
        mdm_keywords = [
            "Medical Decision Making",
            "MDM",
            "Problems Addressed",
            "Data Reviewed",
            "Risk of Complications",
            "straightforward",
            "low complexity",
            "moderate complexity", 
            "high complexity"
        ]
        
        lines = guidelines.split('\n')
        mdm_content = []
        
        for line in lines:
            if any(keyword.lower() in line.lower() for keyword in mdm_keywords):
                mdm_content.append(line)
        
        if mdm_content:
            return '\n'.join(mdm_content)
        else:
            return "MDM complexity information not found in guidelines."
    
    def clear_cache(self):
        """Clear all cached content (useful for testing or when guidelines are updated)"""
        with self._cache_lock:
            self._em_guidelines_cache = None
            self._pdf_guidelines_cache = None
            self._extract_code_requirements.cache_clear()
            self._extract_mdm_content.cache_clear()
            logger.info("Guidelines cache cleared")
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        return {
            "em_guidelines_cached": self._em_guidelines_cache is not None,
            "em_guidelines_size": len(self._em_guidelines_cache) if self._em_guidelines_cache else 0,
            "code_requirements_cache_info": self._extract_code_requirements.cache_info(),
            "mdm_content_cache_info": self._extract_mdm_content.cache_info()
        }


# Global cache instance
_guidelines_cache = GuidelinesCache()


def get_em_coding_guidelines() -> str:
    """
    Get comprehensive E/M coding guidelines from cache.
    
    Returns:
        Complete E/M coding guidelines and standards text
    """
    return _guidelines_cache.get_em_guidelines()


def get_specific_code_requirements(code: str) -> str:
    """
    Get specific requirements and criteria for a particular E/M code from cache.
    
    Args:
        code: The E/M code to get requirements for (99212, 99213, 99214, or 99215)
        
    Returns:
        Detailed requirements, criteria, and documentation standards for the specified code
    """
    return _guidelines_cache.get_specific_code_requirements(code)


def get_mdm_complexity_guide() -> str:
    """
    Get detailed Medical Decision Making (MDM) complexity guidelines from cache.
    
    Returns:
        Comprehensive guide to MDM complexity levels
    """
    return _guidelines_cache.get_mdm_complexity_guide()


def clear_guidelines_cache():
    """Clear the guidelines cache"""
    _guidelines_cache.clear_cache()


def get_cache_statistics() -> dict:
    """Get cache statistics"""
    return _guidelines_cache.get_cache_stats()


async def warm_cache_async():
    """Warm cache asynchronously"""
    return await _guidelines_cache.warm_cache_async()
