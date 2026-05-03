import pytest
import json
from app.src.rule_extractor import RuleBasedExtractor


class TestRuleBasedExtractor:
    """Test rule-based extraction"""
    
    def test_invoice_number_extraction(self):
        """Test invoice number extraction"""
        text = "Invoice #INV-2024-001"
        value, confidence = RuleBasedExtractor.extract_field(text, "invoice_number")
        assert value == "INV-2024-001"
        assert confidence > 0
    
    def test_amount_extraction(self):
        """Test amount extraction"""
        text = "Total Amount: $5,000.00"
        value, confidence = RuleBasedExtractor.extract_field(text, "amount")
        assert "$5,000.00" in str(value)
        assert confidence > 0
    
    def test_date_extraction(self):
        """Test date extraction"""
        text = "Invoice Date: 15-01-2024"
        value, confidence = RuleBasedExtractor.extract_field(text, "date")
        assert "15" in str(value) or "01" in str(value)
        assert confidence > 0
    
    def test_email_extraction(self):
        """Test email extraction"""
        text = "Contact us at support@example.com"
        value, confidence = RuleBasedExtractor.extract_field(text, "email")
        assert value == "support@example.com"
        assert confidence > 0
    
    def test_phone_extraction(self):
        """Test phone extraction"""
        text = "Call us at +1 (555) 123-4567"
        value, confidence = RuleBasedExtractor.extract_field(text, "phone")
        assert value is not None
        assert confidence > 0
    
    def test_extract_all(self):
        """Test extracting all fields"""
        text = """
        Invoice #INV-2024-001
        Date: 15-01-2024
        Email: contact@example.com
        Total: $5,000.00
        Tax ID: 12-3456789
        """
        results = RuleBasedExtractor.extract_all(text)
        assert len(results) > 0
        assert "invoice_number" in results or any("INV" in str(v) for v, _ in results.values())
    
    def test_line_items_extraction(self):
        """Test line items extraction"""
        text = """
        Item 1: Laptop 2 $1000.00 $2000.00
        Item 2: Monitor 1 $300.00 $300.00
        """
        line_items = RuleBasedExtractor.extract_line_items(text)
        assert len(line_items) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
