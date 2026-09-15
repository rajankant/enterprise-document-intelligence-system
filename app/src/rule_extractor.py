import re
from typing import Dict, Tuple, Optional, Any
from datetime import datetime


class RuleBasedExtractor:
    """Rule-based extraction engine using regex patterns"""
    
    # Common patterns
    PATTERNS = {
        "invoice_number": [
            r"(?:Invoice\s*(?:#|Number)?|INV)[\s:#-]*([A-Z0-9][A-Z0-9\-/#]+)",
            r"^[A-Z]{2,4}-\d{4}-\d{3,4}$"
        ],
        "amount": [
            r"(?:Total|Amount|Total Amount|Grand Total)[\s:]*\$?([\d,]+\.?\d{0,2})",
            r"(?:₹|USD|INR)?\s*([0-9,]+\.?\d{0,2})"
        ],
        "date": [
            r"(?:Date|Invoice Date|Issued)[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})",
            r"(\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{4})"
        ],
        "vendor_name": [
            r"(?:Bill From|From|Vendor|Seller)[\s:]*([A-Za-z\s&,\.]+?)(?:\n|$)",
            r"^([A-Za-z\s&,\.]+?)\n.*Invoice"
        ],
        "email": [
            r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            r"(?:Email|Contact|E-mail)\s*[:\-]\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
        ],
        "phone": [
            r"((?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})",
            r"((?:\+\d{1,3}[-.\s]?)?\d{10,})"
        ],
        "tax_id": [
            r"(?:Tax ID|TIN|GST|VAT)[\s:]*([A-Z0-9\-]+)",
            r"(?:GSTIN|PAN)[\s:]*([A-Z0-9]+)"
        ]
    }

    JOB_DESCRIPTION_PATTERNS = {
        "job_title": [
            r"(?:Job Title|Position|Role)\s*[:\-]\s*([^\n]+)",
            r"(?:Hiring|Opening)\s+(?:for\s+)?(?:a|an)?\s*([A-Za-z][A-Za-z\s/+-]+?)(?:\n|$)"
        ],
        "company": [
            r"(?:Company|Organization|Employer)\s*[:\-]\s*([^\n]+)",
            r"(?:About|About Us)\s*[:\-]?\s*([^\n]+)"
        ],
        "location": [
            r"(?:Location|Work Location|Job Location)\s*[:\-]\s*([^\n]+)",
            r"(?:Remote|Hybrid|Onsite)\s*(?:-|,)?\s*([A-Za-z][A-Za-z\s,]+)?"
        ],
        "salary_range": [
            r"(?:Salary|Compensation|CTC|Pay)\s*[:\-]\s*([^\n]+)",
            r"((?:₹|Rs\.?|INR|\$|USD)\s*[\d,.]+(?:\s*[-–]\s*(?:₹|Rs\.?|INR|\$|USD)?\s*[\d,.]+)?)"
        ],
        "requirements": [
            r"(?:Requirements|Qualifications|Skills Required|Required Skills)\s*[:\-]?\s*([\s\S]{0,700}?)(?:\n\s*(?:Responsibilities|Benefits|About|Location|Salary)\b|$)"
        ],
        "responsibilities": [
            r"(?:Responsibilities|Duties|What You(?:'|’)ll Do|Job Description)\s*[:\-]?\s*([\s\S]{0,700}?)(?:\n\s*(?:Requirements|Qualifications|Benefits|About|Location|Salary)\b|$)"
        ],
        "email": PATTERNS["email"],
        "phone": PATTERNS["phone"],
    }
    
    @classmethod
    def extract_field(cls, text: str, field_name: str, case_sensitive: bool = False) -> Tuple[Optional[str], float]:
        """
        Extract a field from text using regex patterns
        
        Args:
            text: Input text to extract from
            field_name: Name of field to extract (key in PATTERNS)
            case_sensitive: Whether to use case-sensitive matching
            
        Returns:
            Tuple of (extracted_value, confidence_score)
        """
        if field_name not in cls.PATTERNS:
            return None, 0.0
        
        patterns = cls.PATTERNS[field_name]
        flags = 0 if case_sensitive else re.IGNORECASE
        
        for pattern in patterns:
            match = re.search(pattern, text, flags)
            if match:
                # Return first capturing group or full match
                value = match.group(1) if match.groups() else match.group(0)
                if field_name == "amount" and "$" in match.group(0) and not value.strip().startswith("$"):
                    value = f"${value}"
                # Confidence based on pattern specificity
                confidence = 0.9 if len(patterns) > 1 else 0.85
                return value.strip(), confidence
        
        return None, 0.0
    
    @classmethod
    def extract_all(cls, text: str, document_type: str = "invoice") -> Dict[str, Tuple[Optional[str], float]]:
        """
        Extract all known fields from text
        
        Args:
            text: Input text
            
        Returns:
            Dictionary of {field_name: (value, confidence)}
        """
        results = {}
        patterns = cls.JOB_DESCRIPTION_PATTERNS if document_type == "job_description" else cls.PATTERNS

        for field_name in patterns.keys():
            value, confidence = cls.extract_field(text, field_name)
            if document_type == "job_description" and field_name in cls.JOB_DESCRIPTION_PATTERNS:
                value, confidence = cls._extract_with_patterns(text, cls.JOB_DESCRIPTION_PATTERNS[field_name])
            if value:
                results[field_name] = (value, confidence)
        
        return results

    @classmethod
    def extract_all_with_attempts(cls, text: str, document_type: str = "invoice") -> Dict[str, Any]:
        """
        Extract all fields with ALL attempts (including failed/low-confidence ones)
        
        Args:
            text: Input text
            document_type: Type of document
            
        Returns:
            Dictionary with successful extractions and all attempts
        """
        successful = {}
        all_attempts = {}
        patterns = cls.JOB_DESCRIPTION_PATTERNS if document_type == "job_description" else cls.PATTERNS

        for field_name, field_patterns in patterns.items():
            attempts = []
            best_value = None
            best_confidence = 0.0
            
            flags = re.IGNORECASE
            
            for pattern in field_patterns:
                match = re.search(pattern, text, flags)
                if match:
                    value = match.group(1) if match.groups() else match.group(0)
                    value = re.sub(r"\s+", " ", value).strip(" -:\t\r\n") if isinstance(value, str) else value
                    
                    # Calculate confidence based on match quality
                    confidence = 0.85 if len(field_patterns) > 1 else 0.75
                    
                    # Validate field-specific requirements
                    confidence = cls._validate_field_quality(field_name, value, confidence)
                    
                    attempts.append({
                        "pattern": pattern[:100],  # First 100 chars
                        "value": value,
                        "confidence": confidence,
                        "matched": True
                    })
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_value = value
            
            all_attempts[field_name] = attempts
            
            if best_value:
                successful[field_name] = (best_value, best_confidence)
        
        return {
            "successful": successful,
            "all_attempts": all_attempts
        }
    
    @classmethod
    def _validate_field_quality(cls, field_name: str, value: str, base_confidence: float) -> float:
        """Validate field quality and adjust confidence score"""
        if not isinstance(value, str):
            return 0.0
        
        # Phone: must have at least 10 digits
        if field_name == "phone":
            digit_count = len(re.sub(r"\D", "", value))
            has_country_code = value.startswith("+") or value.startswith("1-") or value.startswith("91")
            
            if digit_count < 10:
                # Heavy penalty for incomplete phone numbers
                return 0.2  # Very low confidence for partial numbers like "884"
            elif digit_count == 10:
                # Standard 10-digit without country code
                return 0.90
            elif digit_count == 11 and value.startswith("1"):
                # US format with leading 1
                return 0.92
            elif digit_count > 10 and value.startswith("+"):
                # International format with country code (best)
                return 0.95
            else:
                return 0.93  # Other valid formats
        
        # Email: must have valid format with @ and domain
        if field_name == "email":
            if "@" not in value or "." not in value.split("@")[-1]:
                return 0.2
            return 0.95
        
        # Amount: must have numeric value
        if field_name == "amount":
            if not re.search(r"\d", value):
                return 0.2
            return base_confidence
        
        # Date: should have 4-digit year
        if field_name == "date":
            if not re.search(r"\d{4}", value):
                return 0.4
            return base_confidence
        
        return base_confidence

    @classmethod
    def _extract_with_patterns(cls, text: str, patterns: list, case_sensitive: bool = False) -> Tuple[Optional[str], float]:
        flags = 0 if case_sensitive else re.IGNORECASE

        for pattern in patterns:
            match = re.search(pattern, text, flags)
            if match:
                value = match.group(1) if match.groups() else match.group(0)
                value = re.sub(r"\s+", " ", value).strip(" -:\t\r\n")
                if value:
                    return value[:500], 0.85

        return None, 0.0
    
    @classmethod
    def extract_line_items(cls, text: str) -> list:
        """
        Extract line items from invoice text
        Looks for patterns like: description qty price
        """
        # Simple line item extraction
        line_items = []
        lines = text.split('\n')
        
        # Pattern: quantity x price = total
        item_pattern = r"([\w\s]+?)\s+(\d+)\s+[\$₹]?\s*(\d+\.?\d*)\s*(?:[\$₹]?\s*(\d+\.?\d*))?"
        
        for line in lines:
            match = re.search(item_pattern, line)
            if match:
                description, qty, price, total = match.groups()
                line_items.append({
                    "description": description.strip(),
                    "quantity": int(qty),
                    "unit_price": float(price),
                    "total": float(total) if total else float(qty) * float(price)
                })
        
        return line_items


if __name__ == "__main__":
    # Test extraction
    sample_text = """
    Invoice #INV-2024-001
    Date: 2024-01-15
    
    Bill From:
    ABC Company
    Email: contact@abccompany.com
    Phone: +1 (555) 123-4567
    
    Total Amount: $5,000.00
    Tax ID: 12-3456789
    """
    
    results = RuleBasedExtractor.extract_all(sample_text)
    for field, (value, confidence) in results.items():
        print(f"{field}: {value} (confidence: {confidence:.2f})")
