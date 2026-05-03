import re
from datetime import datetime
from typing import Any, Tuple, Optional, Union
from decimal import Decimal, InvalidOperation


class DataValidator:
    """Validate and clean extracted data"""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email format"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if re.match(pattern, email):
            return True, email.lower()
        return False, email
    
    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, str]:
        """Validate and normalize phone number"""
        # Remove all non-digits except +
        cleaned = re.sub(r"[^\d+]", "", phone)
        # Check if it looks like a valid phone (8-15 digits)
        if 8 <= len(cleaned) <= 15:
            return True, cleaned
        return False, phone
    
    @staticmethod
    def validate_amount(amount: Union[str, float, int]) -> Tuple[bool, Optional[float]]:
        """Validate and convert amount to float"""
        if isinstance(amount, (int, float)):
            try:
                value = float(amount)
                if value >= 0:
                    return True, round(value, 2)
                return False, None
            except (ValueError, TypeError):
                return False, None
        
        if isinstance(amount, str):
            # Remove currency symbols and commas
            cleaned = re.sub(r"[^\d\.\-]", "", amount.strip())
            try:
                value = float(cleaned)
                if value >= 0:
                    return True, round(value, 2)
                return False, None
            except ValueError:
                return False, None
        
        return False, None
    
    @staticmethod
    def validate_date(date_str: str, format_list: list = None) -> Tuple[bool, Optional[str]]:
        """Validate and normalize date"""
        if format_list is None:
            format_list = [
                "%d-%m-%Y", "%d/%m/%Y",
                "%m-%d-%Y", "%m/%d/%Y",
                "%Y-%m-%d", "%Y/%m/%d",
                "%d %b %Y", "%d %B %Y",
                "%b %d, %Y", "%B %d, %Y"
            ]
        
        date_str = date_str.strip()
        
        for fmt in format_list:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return True, parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        return False, date_str
    
    @staticmethod
    def validate_invoice_number(invoice_num: str) -> Tuple[bool, str]:
        """Validate invoice number format"""
        # Remove extra spaces
        cleaned = invoice_num.strip()
        
        # Check if it contains alphanumeric and allowed special chars
        if re.match(r"^[A-Z0-9\-/#]*$", cleaned, re.IGNORECASE):
            return True, cleaned.upper()
        return False, cleaned
    
    @staticmethod
    def validate_tax_id(tax_id: str) -> Tuple[bool, str]:
        """Validate tax ID format"""
        cleaned = tax_id.strip().upper()
        
        # Basic validation: alphanumeric with dashes
        if re.match(r"^[A-Z0-9\-]*$", cleaned) and len(cleaned) >= 5:
            return True, cleaned
        return False, cleaned
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Trim
        text = text.strip()
        return text
    
    @staticmethod
    def normalize_currency(amount: str) -> Optional[float]:
        """Extract and normalize currency amount"""
        # Remove all non-numeric except decimal point
        match = re.search(r"[\d,]+\.?\d{0,2}", amount)
        if match:
            cleaned = match.group().replace(",", "")
            try:
                return round(float(cleaned), 2)
            except ValueError:
                return None
        return None


class ConfidenceScorer:
    """Calculate confidence scores for extracted fields"""
    
    @staticmethod
    def score_extraction(
        value: Any,
        source: str,
        validation_passed: bool,
        pattern_matches: int = 1
    ) -> float:
        """
        Calculate confidence score
        
        Args:
            value: Extracted value
            source: Source of extraction (rule/llm/hybrid)
            validation_passed: Whether validation passed
            pattern_matches: Number of patterns that matched
            
        Returns:
            Confidence score between 0 and 1
        """
        base_score = {
            "rule": 0.85,
            "llm": 0.80,
            "hybrid": 0.90
        }.get(source, 0.50)
        
        # Boost for validation
        if validation_passed:
            base_score += 0.05
        else:
            base_score -= 0.10
        
        # Boost for multiple pattern matches
        if pattern_matches > 1:
            base_score += 0.05
        
        # Ensure within bounds
        return max(0.0, min(1.0, base_score))
    
    @staticmethod
    def score_extraction_quality(extracted_fields: dict) -> float:
        """
        Calculate overall extraction quality score
        
        Args:
            extracted_fields: Dictionary of {field: (value, confidence)}
            
        Returns:
            Overall confidence score (0-1)
        """
        if not extracted_fields:
            return 0.0
        
        confidences = []
        for field in extracted_fields.values():
            if hasattr(field, "confidence"):
                confidences.append(field.confidence)
            elif isinstance(field, tuple):
                confidences.append(field[1] if len(field) > 1 else field[0])

        return sum(confidences) / len(confidences) if confidences else 0.0


if __name__ == "__main__":
    # Test validators
    print("Email validation:")
    print(DataValidator.validate_email("test@example.com"))
    
    print("\nAmount validation:")
    print(DataValidator.validate_amount("$5,000.00"))
    
    print("\nDate validation:")
    print(DataValidator.validate_date("15-01-2024"))
    
    print("\nConfidence scoring:")
    score = ConfidenceScorer.score_extraction("INV-2024-001", "rule", True, 2)
    print(f"Score: {score:.2f}")
