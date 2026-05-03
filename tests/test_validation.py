import pytest
from app.src.validation import DataValidator, ConfidenceScorer


class TestDataValidator:
    """Test data validation and cleaning"""
    
    def test_validate_email_valid(self):
        """Test valid email validation"""
        is_valid, email = DataValidator.validate_email("test@example.com")
        assert is_valid
        assert email == "test@example.com"
    
    def test_validate_email_invalid(self):
        """Test invalid email validation"""
        is_valid, email = DataValidator.validate_email("invalid-email")
        assert not is_valid
    
    def test_validate_phone_valid(self):
        """Test valid phone validation"""
        is_valid, phone = DataValidator.validate_phone("+1 (555) 123-4567")
        assert is_valid
        assert len(phone) >= 10
    
    def test_validate_amount_string(self):
        """Test amount validation from string"""
        is_valid, amount = DataValidator.validate_amount("$5,000.00")
        assert is_valid
        assert amount == 5000.00
    
    def test_validate_amount_float(self):
        """Test amount validation from float"""
        is_valid, amount = DataValidator.validate_amount(5000.50)
        assert is_valid
        assert amount == 5000.50
    
    def test_validate_amount_negative(self):
        """Test negative amount validation"""
        is_valid, amount = DataValidator.validate_amount("-100")
        assert not is_valid
    
    def test_validate_date_valid(self):
        """Test valid date validation"""
        is_valid, date = DataValidator.validate_date("15-01-2024")
        assert is_valid
        assert "2024" in str(date)
    
    def test_validate_invoice_number(self):
        """Test invoice number validation"""
        is_valid, inv = DataValidator.validate_invoice_number("INV-2024-001")
        assert is_valid
        assert inv == "INV-2024-001"
    
    def test_validate_tax_id(self):
        """Test tax ID validation"""
        is_valid, tax_id = DataValidator.validate_tax_id("12-3456789")
        assert is_valid
    
    def test_clean_text(self):
        """Test text cleaning"""
        dirty_text = "  This   has   extra    spaces  "
        clean = DataValidator.clean_text(dirty_text)
        assert clean == "This has extra spaces"
    
    def test_normalize_currency(self):
        """Test currency normalization"""
        amount = DataValidator.normalize_currency("Total: $5,000.50 USD")
        assert amount == 5000.50


class TestConfidenceScorer:
    """Test confidence scoring"""
    
    def test_score_extraction_rule_valid(self):
        """Test scoring for valid rule extraction"""
        score = ConfidenceScorer.score_extraction("INV-001", "rule", True)
        assert 0.8 <= score <= 1.0
    
    def test_score_extraction_rule_invalid(self):
        """Test scoring for invalid rule extraction"""
        score = ConfidenceScorer.score_extraction("INV-001", "rule", False)
        assert 0.0 <= score < 0.8
    
    def test_score_extraction_llm(self):
        """Test scoring for LLM extraction"""
        score = ConfidenceScorer.score_extraction("INV-001", "llm", True)
        assert 0.7 <= score <= 1.0
    
    def test_score_extraction_hybrid(self):
        """Test scoring for hybrid extraction"""
        score = ConfidenceScorer.score_extraction("INV-001", "hybrid", True)
        assert score >= 0.85
    
    def test_score_extraction_quality(self):
        """Test overall extraction quality score"""
        fields = {
            "field1": (0.9,),
            "field2": (0.8,),
            "field3": (0.95,)
        }
        # Convert to proper format
        fields_dict = {}
        for k, v in fields.items():
            fields_dict[k] = v
        
        score = ConfidenceScorer.score_extraction_quality(fields_dict)
        assert 0.8 <= score <= 1.0
    
    def test_score_extraction_quality_empty(self):
        """Test scoring for empty extraction"""
        score = ConfidenceScorer.score_extraction_quality({})
        assert score == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
