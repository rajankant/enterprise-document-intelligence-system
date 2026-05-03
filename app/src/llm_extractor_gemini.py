import json
import os
from typing import Dict, Optional


class LLMExtractor:
    """LLM-based extraction using Google Gemini (Free API)"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
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
    
    def extract_from_text(
        self,
        text: str,
        document_type: str = "invoice",
        schema: Optional[Dict[str, str]] = None
    ) -> Dict[str, tuple]:
        """
        Extract structured data using Gemini LLM
        
        Args:
            text: Raw document text
            document_type: Type of document
            schema: Optional schema defining fields to extract
            
        Returns:
            Dict of {field_name: (value, confidence)}
        """
        if schema is None:
            schema = self._get_default_schema(document_type)
        
        prompt = self._build_prompt(text, document_type, schema)
        
        try:
            response = self.model.generate_content(prompt)
            content = response.text
            
            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = content[json_start:json_end]
                extracted_json = json.loads(json_str)
            else:
                extracted_json = json.loads(content)
            
            # Convert to standard format
            results = {}
            for field, value in extracted_json.items():
                if not field.endswith('_confidence') and value is not None:
                    confidence = extracted_json.get(f"{field}_confidence", 0.85)
                    results[field] = (value, confidence)
            
            return results
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse Gemini response as JSON: {str(e)}")
            return {}
        except Exception as e:
            print(f"Gemini API Error: {str(e)}")
            return {}
    
    def merge_extractions(
        self,
        rule_results: Dict[str, tuple],
        llm_results: Dict[str, tuple]
    ) -> Dict[str, tuple]:
        """Merge rule-based and LLM extraction results"""
        merged = {}
        all_fields = set(rule_results.keys()) | set(llm_results.keys())
        
        for field in all_fields:
            rule_value, rule_conf = rule_results.get(field, (None, 0.0))
            llm_value, llm_conf = llm_results.get(field, (None, 0.0))
            
            if rule_conf >= llm_conf and rule_value:
                merged[field] = (rule_value, rule_conf)
            elif llm_value:
                merged[field] = (llm_value, llm_conf)
            else:
                merged[field] = (rule_value or llm_value, max(rule_conf, llm_conf))
        
        return merged
    
    def _build_prompt(self, text: str, document_type: str, schema: Dict[str, str]) -> str:
        """Build extraction prompt for Gemini"""
        fields_desc = "\n".join([f"- {field}: {desc}" for field, desc in schema.items()])
        
        return f"""Extract structured data from the following {document_type} document.

Return ONLY a valid JSON object with the following fields:
{fields_desc}

For each field, include a confidence score (0-1) as "{{field}}_confidence".
If a field is not found, use null for the value.

Document text:
{text[:3000]}

Return only valid JSON, no other text."""
    
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
