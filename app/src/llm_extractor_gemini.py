import json
import os
import logging
import base64
import hashlib
import time
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Any
from datetime import datetime
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=False)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LLMExtractor:
    """Enhanced LLM-based extraction using Google Gemini with caching, retry logic, and validation"""
    
    def __init__(
        self,
        api_key = os.getenv("GEMINI_API_KEY"),
        model: str = "gemini-1.5-flash",
        enable_cache: bool = True,
        cache_dir: str = ".cache/llm_extractions",
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize LLM Extractor
        
        Args:
            api_key: Gemini API key (or use GEMINI_API_KEY env var)
            model: Model name (default: gemini-1.5-flash)
            enable_cache: Enable response caching
            cache_dir: Directory for cache files
            max_retries: Max retry attempts on API failures
            retry_delay: Initial delay between retries (exponential backoff)
        """
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Set it in .env or pass as parameter.\n"
                "Get free key at https://ai.google.dev"
            )
        
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise ImportError(
                "google-generativeai is not installed. Run `pip install -r requirements.txt` "
                "from the project root before enabling LLM extraction."
            ) from exc

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model)
        self.model_name = model
        
        # Caching configuration
        self.enable_cache = enable_cache
        self.cache_dir = Path(cache_dir)
        if self.enable_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Retry configuration
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        logger.info(f"LLMExtractor initialized with model: {model}, caching: {enable_cache}")
    
    def extract_from_text(
        self,
        text: str,
        document_type: str = "invoice",
        schema: Optional[Dict[str, str]] = None,
        custom_prompt: Optional[str] = None,
        validate: bool = True
    ) -> Dict[str, Tuple[Any, float]]:
        """
        Extract structured data from text using Gemini LLM
        
        Args:
            text: Raw document text
            document_type: Type of document
            schema: Optional schema defining fields to extract
            custom_prompt: Custom extraction instructions
            validate: Validate extracted data against schema
            
        Returns:
            Dict of {field_name: (value, confidence)}
        """
        if schema is None:
            schema = self._get_default_schema(document_type)
        
        # Check cache
        cache_key = self._generate_cache_key(text, document_type, schema)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            logger.info(f"Cache hit for {document_type}")
            return cached_result
        
        prompt = custom_prompt or self._build_prompt(text, document_type, schema)
        
        # Extract with retry logic
        results = self._extract_with_retry(text, prompt, schema)
        
        # Validate results
        if validate and results:
            results = self._validate_results(results, schema)
        
        # Cache results
        if self.enable_cache and results:
            self._cache_result(cache_key, results)
        
        logger.info(f"Extracted {len(results)} fields from {document_type}")
        return results
    
    def extract_from_image(
        self,
        image_path: str,
        document_type: str = "invoice",
        schema: Optional[Dict[str, str]] = None,
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Tuple[Any, float]]:
        """
        Extract structured data directly from image file using Gemini vision
        
        Args:
            image_path: Path to image file
            document_type: Type of document
            schema: Optional schema defining fields to extract
            custom_prompt: Custom extraction instructions
            
        Returns:
            Dict of {field_name: (value, confidence)}
        """
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return {}
        
        if schema is None:
            schema = self._get_default_schema(document_type)
        
        try:
            # Encode image to base64
            with open(image_path, "rb") as img_file:
                image_data = base64.standard_b64encode(img_file.read()).decode("utf-8")
            
            # Get image MIME type
            ext = Path(image_path).suffix.lower()
            mime_types = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp"
            }
            mime_type = mime_types.get(ext, "image/jpeg")
            
            prompt = custom_prompt or self._build_prompt("", document_type, schema, is_image=True)
            
            # Send image to Gemini
            content = [
                {"type": "image", "mime_type": mime_type, "data": image_data},
                {"type": "text", "text": prompt}
            ]
            
            result = self._send_to_gemini(content)
            
            # Parse response
            results = self._parse_response(result, schema)
            logger.info(f"Extracted {len(results)} fields from image: {image_path}")
            return results
            
        except Exception as e:
            logger.error(f"Error extracting from image {image_path}: {str(e)}")
            return {}
    
    def batch_extract(
        self,
        texts: List[str],
        document_type: str = "invoice",
        schema: Optional[Dict[str, str]] = None,
        show_progress: bool = True
    ) -> List[Dict[str, Tuple[Any, float]]]:
        """
        Extract from multiple documents
        
        Args:
            texts: List of document texts
            document_type: Type of document
            schema: Optional schema
            show_progress: Show progress indicator
            
        Returns:
            List of extraction results
        """
        results = []
        total = len(texts)
        
        for idx, text in enumerate(texts):
            if show_progress:
                logger.info(f"Processing {idx + 1}/{total}")
            
            result = self.extract_from_text(text, document_type, schema)
            results.append(result)
        
        logger.info(f"Batch extraction completed: {total} documents processed")
        return results
    
    def batch_extract_images(
        self,
        image_paths: List[str],
        document_type: str = "invoice",
        schema: Optional[Dict[str, str]] = None,
        show_progress: bool = True
    ) -> List[Dict[str, Tuple[Any, float]]]:
        """
        Extract from multiple image files
        
        Args:
            image_paths: List of image file paths
            document_type: Type of document
            schema: Optional schema
            show_progress: Show progress indicator
            
        Returns:
            List of extraction results
        """
        results = []
        total = len(image_paths)
        
        for idx, image_path in enumerate(image_paths):
            if show_progress:
                logger.info(f"Processing {idx + 1}/{total}: {image_path}")
            
            result = self.extract_from_image(image_path, document_type, schema)
            results.append(result)
        
        logger.info(f"Batch image extraction completed: {total} images processed")
        return results
    
    def merge_extractions(
        self,
        rule_results: Dict[str, Tuple[Any, float]],
        llm_results: Dict[str, Tuple[Any, float]],
        rule_weight: float = 0.6,
        llm_weight: float = 0.4
    ) -> Dict[str, Tuple[Any, float]]:
        """
        Merge rule-based and LLM extraction results with weighted confidence
        
        Args:
            rule_results: Results from rule-based extraction
            llm_results: Results from LLM extraction
            rule_weight: Weight for rule-based confidence (0-1)
            llm_weight: Weight for LLM confidence (0-1)
            
        Returns:
            Merged results with adjusted confidence scores
        """
        merged = {}
        all_fields = set(rule_results.keys()) | set(llm_results.keys())
        
        for field in all_fields:
            rule_value, rule_conf = rule_results.get(field, (None, 0.0))
            llm_value, llm_conf = llm_results.get(field, (None, 0.0))
            
            # Apply weights
            weighted_rule_conf = rule_conf * rule_weight if rule_value else 0
            weighted_llm_conf = llm_conf * llm_weight if llm_value else 0
            
            # Choose best value based on weighted confidence
            if weighted_rule_conf >= weighted_llm_conf and rule_value:
                merged[field] = (rule_value, min(1.0, weighted_rule_conf))
            elif llm_value:
                merged[field] = (llm_value, min(1.0, weighted_llm_conf))
            else:
                merged[field] = (rule_value or llm_value, max(weighted_rule_conf, weighted_llm_conf))
        
        logger.info(f"Merged {len(merged)} fields from rule-based and LLM extraction")
        return merged
    
    def _extract_with_retry(
        self,
        text: str,
        prompt: str,
        schema: Dict[str, str]
    ) -> Dict[str, Tuple[Any, float]]:
        """Extract with retry logic and exponential backoff"""
        for attempt in range(self.max_retries):
            try:
                result = self._send_to_gemini(prompt)
                parsed = self._parse_response(result, schema)
                return parsed
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Extraction attempt {attempt + 1} failed: {str(e)}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Extraction failed after {self.max_retries} attempts: {str(e)}")
                    return {}
        
        return {}
    
    def _send_to_gemini(self, content: Any) -> str:
        """Send request to Gemini API"""
        response = self.model.generate_content(content)
        return response.text
    
    def _parse_response(self, response: str, schema: Dict[str, str]) -> Dict[str, Tuple[Any, float]]:
        """Parse Gemini response to extract JSON"""
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
            else:
                json_str = response
            
            extracted_json = json.loads(json_str)
            
            # Convert to standard format
            results = {}
            for field, value in extracted_json.items():
                if not field.endswith('_confidence') and value is not None:
                    confidence = extracted_json.get(f"{field}_confidence", 0.85)
                    confidence = max(0.0, min(1.0, float(confidence)))  # Clamp to 0-1
                    results[field] = (value, confidence)
            
            return results
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {str(e)}")
            return {}
    
    def _validate_results(
        self,
        results: Dict[str, Tuple[Any, float]],
        schema: Dict[str, str]
    ) -> Dict[str, Tuple[Any, float]]:
        """Validate extracted results against schema"""
        validated = {}
        
        for field, (value, conf) in results.items():
            if field in schema:
                # Basic validation: check if value is not empty
                if value and str(value).strip():
                    validated[field] = (value, conf)
                    logger.debug(f"✓ Validated: {field} = {value}")
                else:
                    logger.debug(f"✗ Invalid: {field} is empty")
            else:
                logger.debug(f"⚠ Unknown field: {field}")
        
        return validated
    
    def _generate_cache_key(self, text: str, document_type: str, schema: Dict[str, str]) -> str:
        """Generate cache key for extraction"""
        content = f"{text[:500]}_{document_type}_{json.dumps(schema, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Tuple[Any, float]]]:
        """Retrieve cached extraction result"""
        if not self.enable_cache:
            return None
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    # Convert tuples back from lists
                    return {k: (v[0], v[1]) for k, v in data.items()}
            except Exception as e:
                logger.warning(f"Error loading cache: {str(e)}")
                return None
        
        return None
    
    def _cache_result(self, cache_key: str, results: Dict[str, Tuple[Any, float]]) -> None:
        """Cache extraction results"""
        if not self.enable_cache:
            return
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            # Convert tuples to lists for JSON serialization
            serializable = {k: list(v) for k, v in results.items()}
            with open(cache_file, 'w') as f:
                json.dump(serializable, f, indent=2)
            logger.debug(f"Cached results to {cache_file}")
        except Exception as e:
            logger.warning(f"Error caching results: {str(e)}")
    
    def clear_cache(self) -> None:
        """Clear all cached results"""
        if self.enable_cache and self.cache_dir.exists():
            import shutil
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Cache cleared")
    
    def _build_prompt(
        self,
        text: str,
        document_type: str,
        schema: Dict[str, str],
        is_image: bool = False
    ) -> str:
        """Build extraction prompt for Gemini"""
        fields_desc = "\n".join([f"- {field}: {desc}" for field, desc in schema.items()])
        
        if is_image:
            return f"""Analyze this {document_type} image and extract structured data.

Return ONLY a valid JSON object with the following fields:
{fields_desc}

For each field, include a confidence score (0-1) as "{{field}}_confidence".
If a field is not found, use null for the value.

Return only valid JSON, no other text or explanation."""
        
        return f"""Extract structured data from the following {document_type} document.

Return ONLY a valid JSON object with the following fields:
{fields_desc}

For each field, include a confidence score (0-1) as "{{field}}_confidence".
If a field is not found, use null for the value.

Document text:
{text[:3000]}

Return only valid JSON, no other text or explanation."""
    
    def _get_default_schema(self, document_type: str) -> Dict[str, str]:
        """Get default extraction schema for document type"""
        schemas = {
            "invoice": {
                "invoice_number": "Unique invoice identifier",
                "invoice_date": "Date issued (YYYY-MM-DD)",
                "vendor_name": "Company issuing invoice",
                "vendor_email": "Vendor email",
                "vendor_phone": "Vendor phone",
                "customer_name": "Customer/buyer name",
                "amount": "Total amount",
                "currency": "Currency (USD, INR, etc.)",
                "due_date": "Payment due date (YYYY-MM-DD)",
                "tax_id": "Tax ID"
            },
            "bill": {
                "bill_number": "Bill ID",
                "bill_date": "Bill date",
                "vendor": "Service provider",
                "customer": "Bill recipient",
                "total_amount": "Amount owed",
                "due_date": "Payment deadline",
                "services": "Services provided"
            },
            "receipt": {
                "receipt_number": "Receipt ID",
                "transaction_date": "Transaction date",
                "merchant": "Store name",
                "items": "Items purchased",
                "total": "Total amount",
                "payment_method": "Payment method"
            },
            "job_description": {
                "job_title": "Position title",
                "company": "Company name",
                "location": "Job location",
                "salary_range": "Expected salary",
                "requirements": "Key requirements",
                "responsibilities": "Main duties",
                "benefits": "Benefits offered"
            }
        }
        
        return schemas.get(document_type, schemas["invoice"])
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get statistics about cached extractions"""
        if not self.enable_cache or not self.cache_dir.exists():
            return {"cache_enabled": self.enable_cache, "cached_documents": 0}
        
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            "cache_enabled": self.enable_cache,
            "cached_documents": len(cache_files),
            "cache_size_mb": total_size / (1024 * 1024),
            "cache_dir": str(self.cache_dir),
            "model": self.model_name,
            "max_retries": self.max_retries
        }
