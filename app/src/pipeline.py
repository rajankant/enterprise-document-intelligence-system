import time
from typing import Dict, Optional, Any
from pathlib import Path
import traceback

from app.src.ocr import extract_text_from_pdf
from app.src.rule_extractor import RuleBasedExtractor
from app.src.validation import DataValidator, ConfidenceScorer
from app.models.schemas import DocumentExtraction, ExtractedField, ExtractionSource


class ExtractionPipeline:
    """Main extraction pipeline: OCR → Rule → Validation → Scoring"""
    
    def __init__(self):
        self.validator = DataValidator()
        self.scorer = ConfidenceScorer()
    
    def process_document(self, pdf_path: str, document_type: str = "invoice") -> DocumentExtraction:
        """
        Process a document through the entire pipeline
        
        Args:
            pdf_path: Path to PDF file
            document_type: Type of document (invoice, bill, receipt, etc.)
            
        Returns:
            DocumentExtraction object with results
        """
        start_time = time.time()
        
        try:
            # Step 1: Extract text using OCR
            raw_text = extract_text_from_pdf(pdf_path)
            page_count = self._get_page_count(pdf_path)
            
            # Step 2: Extract using rules
            extracted_data = RuleBasedExtractor.extract_all(raw_text)
            
            # Step 3: Validate and clean extracted data
            validated_fields = self._validate_extracted_data(extracted_data)
            
            # Step 4: Calculate confidence scores
            overall_confidence = self.scorer.score_extraction_quality(validated_fields)
            
            # Build final result
            result = DocumentExtraction(
                document_name=Path(pdf_path).name,
                extracted_fields=validated_fields,
                overall_confidence=round(overall_confidence, 2),
                raw_text=raw_text[:1000],  # First 1000 chars
                page_count=page_count,
                processing_time=round(time.time() - start_time, 2),
                error=None
            )
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            return DocumentExtraction(
                document_name=Path(pdf_path).name,
                extracted_fields={},
                overall_confidence=0.0,
                raw_text="",
                page_count=0,
                processing_time=round(processing_time, 2),
                error=str(e)
            )
    
    def _validate_extracted_data(self, extracted_data: Dict[str, tuple]) -> Dict[str, ExtractedField]:
        """
        Validate and convert extracted data
        
        Args:
            extracted_data: Dict of {field: (value, confidence)}
            
        Returns:
            Dict of {field: ExtractedField}
        """
        validated_fields = {}
        
        for field_name, (value, base_confidence) in extracted_data.items():
            if not value:
                continue
            
            # Validate based on field type
            is_valid, cleaned_value = self._validate_field(field_name, value)
            
            # Calculate final confidence
            final_confidence = self.scorer.score_extraction(
                cleaned_value,
                source="rule",
                validation_passed=is_valid
            )
            
            # Create ExtractedField
            extracted_field = ExtractedField(
                name=field_name,
                value=cleaned_value if is_valid else value,
                confidence=round(final_confidence, 2),
                source=ExtractionSource.RULE,
                raw_text=str(value)
            )
            
            validated_fields[field_name] = extracted_field
        
        return validated_fields
    
    def _validate_field(self, field_name: str, value: Any) -> tuple:
        """
        Validate individual field based on type
        
        Args:
            field_name: Name of field
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, cleaned_value)
        """
        validators = {
            "email": self.validator.validate_email,
            "phone": self.validator.validate_phone,
            "amount": self.validator.validate_amount,
            "date": self.validator.validate_date,
            "invoice_number": self.validator.validate_invoice_number,
            "tax_id": self.validator.validate_tax_id,
        }
        
        if field_name in validators:
            is_valid, cleaned_value = validators[field_name](str(value))
            return is_valid, cleaned_value
        
        # Default validation: just clean text
        return True, self.validator.clean_text(str(value))
    
    def _get_page_count(self, pdf_path: str) -> int:
        """Get total page count of PDF"""
        try:
            import fitz
            doc = fitz.open(pdf_path)
            count = len(doc)
            doc.close()
            return count
        except Exception:
            return 1


if __name__ == "__main__":
    # Test pipeline
    pdf_path = r"C:\Users\kashy\Projects\AI Projects\ai-document-intelligence\enterprise-document-intelligence-system\app\input\JD-AIPython (1).pdf"
    
    pipeline = ExtractionPipeline()
    result = pipeline.process_document(pdf_path)
    
    print(f"Document: {result.document_name}")
    print(f"Pages: {result.page_count}")
    print(f"Confidence: {result.overall_confidence}")
    print(f"Time: {result.processing_time}s")
    print(f"\nExtracted Fields:")
    for field_name, field in result.extracted_fields.items():
        print(f"  {field_name}: {field.value} (confidence: {field.confidence})")
    if result.error:
        print(f"Error: {result.error}")
