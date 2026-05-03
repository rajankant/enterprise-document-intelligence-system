import pytest
import os
from pathlib import Path
from app.src.pipeline import ExtractionPipeline


class TestExtractionPipeline:
    """Test end-to-end extraction pipeline"""
    
    @pytest.fixture
    def pipeline(self):
        """Create pipeline instance"""
        return ExtractionPipeline()
    
    @pytest.fixture
    def sample_pdf_path(self):
        """Get path to sample PDF"""
        pdf_path = r"C:\Users\kashy\Projects\AI Projects\ai-document-intelligence\enterprise-document-intelligence-system\app\input\JD-AIPython (1).pdf"
        return pdf_path if os.path.exists(pdf_path) else None
    
    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initialization"""
        assert pipeline is not None
        assert pipeline.validator is not None
        assert pipeline.scorer is not None
    
    def test_process_document(self, pipeline, sample_pdf_path):
        """Test document processing"""
        if not sample_pdf_path:
            pytest.skip("Sample PDF not found")
        
        result = pipeline.process_document(sample_pdf_path, "job_description")
        
        assert result is not None
        assert result.document_name is not None
        assert result.page_count > 0
        assert result.processing_time > 0
        assert 0 <= result.overall_confidence <= 1
    
    def test_process_document_with_error_handling(self, pipeline):
        """Test error handling for non-existent file"""
        result = pipeline.process_document("non_existent_file.pdf")
        
        assert result.error is not None
        assert result.overall_confidence == 0.0
        assert len(result.extracted_fields) == 0
    
    def test_validate_extracted_data(self, pipeline):
        """Test data validation in pipeline"""
        extracted_data = {
            "invoice_number": ("INV-2024-001", 0.9),
            "amount": ("$5,000.00", 0.85),
            "email": ("test@example.com", 0.95)
        }
        
        validated = pipeline._validate_extracted_data(extracted_data)
        
        assert len(validated) > 0
        for field_name, field in validated.items():
            assert field.name == field_name
            assert 0 <= field.confidence <= 1
    
    def test_validate_field_email(self, pipeline):
        """Test email field validation"""
        is_valid, value = pipeline._validate_field("email", "test@example.com")
        assert is_valid
        assert "test@example.com" in str(value)
    
    def test_validate_field_amount(self, pipeline):
        """Test amount field validation"""
        is_valid, value = pipeline._validate_field("amount", "$5,000.00")
        assert is_valid
        assert float(value) == 5000.00
    
    def test_get_page_count(self, pipeline, sample_pdf_path):
        """Test page count detection"""
        if not sample_pdf_path:
            pytest.skip("Sample PDF not found")
        
        page_count = pipeline._get_page_count(sample_pdf_path)
        assert page_count > 0
    
    def test_multiple_documents(self, pipeline, sample_pdf_path):
        """Test processing multiple documents"""
        if not sample_pdf_path:
            pytest.skip("Sample PDF not found")
        
        results = []
        for _ in range(2):
            result = pipeline.process_document(sample_pdf_path)
            results.append(result)
        
        assert len(results) == 2
        for result in results:
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
