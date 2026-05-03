import re
from typing import Dict, Tuple, Optional
from datetime import datetime


class RuleBasedExtractor:
    """Rule-based extraction engine using regex patterns"""
    
    # Common patterns
    PATTERNS = {
        "invoice_number": [
            r"(?:Invoice|INV|Invoice #|Invoice Number)[\s:]*([A-Z0-9\-]+)",
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
            r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
        ],
        "phone": [
            r"(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})",
            r"(?:\+\d{1,3}[-.\s]?)?\d{10,}"
        ],
        "tax_id": [
            r"(?:Tax ID|TIN|GST|VAT)[\s:]*([A-Z0-9\-]+)",
            r"(?:GSTIN|PAN)[\s:]*([A-Z0-9]+)"
        ]
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
                # Confidence based on pattern specificity
                confidence = 0.9 if len(patterns) > 1 else 0.85
                return value.strip(), confidence
        
        return None, 0.0
    
    @classmethod
    def extract_all(cls, text: str) -> Dict[str, Tuple[Optional[str], float]]:
        """
        Extract all known fields from text
        
        Args:
            text: Input text
            
        Returns:
            Dictionary of {field_name: (value, confidence)}
        """
        results = {}
        for field_name in cls.PATTERNS.keys():
            value, confidence = cls.extract_field(text, field_name)
            if value:
                results[field_name] = (value, confidence)
        
        return results
    
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
