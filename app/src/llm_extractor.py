import json
import os
from typing import Dict, Optional, Any
from datetime import datetime
from openai import OpenAI, APIError

from app.models.schemas import ExtractedField, ExtractionSource


class LLMExtractor:
    """LLM-based extraction using OpenAI"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found. Set it in .env or pass as parameter.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
    
    def extract_from_text(
        self,
        text: str,
        document_type: str = "invoice",
        schema: Optional[Dict[str, str]] = None
    ) -> Dict[str, tuple]:
        """
        Extract structured data using LLM
        
        Args:
            text: Raw document text
            document_type: Type of document (invoice, bill, receipt, etc.)
            schema: Optional schema defining fields to extract
            
        Returns:
            Dict of {field_name: (value, confidence)}
        """
        if schema is None:
            schema = self._get_default_schema(document_type)
        
        prompt = self._build_prompt(text, document_type, schema)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert document extraction system. Extract information accurately and return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            extracted_json = json.loads(content)
            
            # Convert to standard format
            results = {}
            for field, value in extracted_json.items():
                # Confidence from LLM
                confidence = extracted_json.get(f"{field}_confidence", 0.85)
                results[field] = (value, confidence)
            
            return results
            
        except APIError as e:
            print(f"OpenAI API Error: {str(e)}")
            return {}
        except json.JSONDecodeError:
            print("Failed to parse LLM response as JSON")
            return {}
    
    def merge_extractions(
        self,
        rule_results: Dict[str, tuple],
        llm_results: Dict[str, tuple]
    ) -> Dict[str, tuple]:
        """
        Merge rule-based and LLM extraction results
        
        Args:
            rule_results: Results from rule-based extraction
            llm_results: Results from LLM extraction
            
        Returns:
            Merged results with best confidence scores
        """
        merged = {}
        all_fields = set(rule_results.keys()) | set(llm_results.keys())
        
        for field in all_fields:
            rule_value, rule_conf = rule_results.get(field, (None, 0.0))
            llm_value, llm_conf = llm_results.get(field, (None, 0.0))
            
            # Choose based on confidence
            if rule_conf >= llm_conf and rule_value:
                merged[field] = (rule_value, rule_conf)
            elif llm_value:
                merged[field] = (llm_value, llm_conf)
            else:
                merged[field] = (rule_value or llm_value, max(rule_conf, llm_conf))
        
        return merged
    
    def _build_prompt(self, text: str, document_type: str, schema: Dict[str, str]) -> str:
        """Build extraction prompt for LLM"""
        fields_desc = "\n".join([f"- {field}: {desc}" for field, desc in schema.items()])
        
        return f"""
Extract structured data from the following {document_type} document.

Return a JSON object with the following fields:
{fields_desc}

For each field, also include a confidence score (0-1) as "{field}_confidence".

Document text:
{text[:3000]}

Return only valid JSON, no other text.
"""
    
    def _get_default_schema(self, document_type: str) -> Dict[str, str]:
        """Get default extraction schema for document type"""
        schemas = {
            "invoice": {
                "invoice_number": "Unique invoice identifier",
                "invoice_date": "Date the invoice was issued (YYYY-MM-DD format)",
                "vendor_name": "Name of the company issuing the invoice",
                "vendor_email": "Email address of vendor",
                "vendor_phone": "Phone number of vendor",
                "customer_name": "Name of customer/buyer",
                "amount": "Total amount due (numeric value)",
                "currency": "Currency (USD, INR, etc.)",
                "due_date": "Payment due date (YYYY-MM-DD format)",
                "tax_id": "Tax identification number",
                "line_items": "List of items with quantity and price"
            },
            "bill": {
                "bill_number": "Bill identifier",
                "bill_date": "Date of bill",
                "vendor": "Service provider name",
                "customer": "Bill recipient",
                "total_amount": "Amount owed",
                "due_date": "Payment deadline",
                "services": "Services or goods provided"
            },
            "receipt": {
                "receipt_number": "Receipt ID",
                "transaction_date": "Date of transaction",
                "merchant": "Store or business name",
                "items": "List of purchased items",
                "total": "Total purchase amount",
                "payment_method": "How payment was made"
            },
            "job_description": {
                "job_title": "Position title",
                "company": "Hiring company",
                "location": "Job location",
                "salary_range": "Expected salary",
                "requirements": "Key requirements",
                "responsibilities": "Main job duties",
                "benefits": "Offered benefits"
            }
        }
        
        return schemas.get(document_type, schemas["invoice"])


if __name__ == "__main__":
    # Test LLM extraction
    sample_text = """
    Invoice #INV-2024-001
    Date: January 15, 2024
    
    Bill From:
    ABC Company
    Email: contact@abccompany.com
    Phone: +1 (555) 123-4567
    Tax ID: 12-3456789
    
    Bill To:
    XYZ Corporation
    
    Items:
    Item 1: Software License - 5 x $200 = $1000
    Item 2: Support Services - 1 x $2000 = $2000
    
    Total Amount: $5,000.00
    Due Date: February 15, 2024
    """
    
    # Note: This requires OPENAI_API_KEY environment variable
    # extractor = LLMExtractor()
    # results = extractor.extract_from_text(sample_text, "invoice")
    # print("LLM Results:", results)
