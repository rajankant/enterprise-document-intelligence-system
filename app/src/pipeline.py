import time
from typing import Dict, Optional
from pathlib import Path

from app.src.ocr import extract_text_from_pdf
from app.src.rule_extractor import RuleBasedExtractor
from app.src.validation import DataValidator, ConfidenceScorer
from app.src.llm_extractor_gemini import LLMExtractor
from app.models.schemas import DocumentExtraction, ExtractedField, ExtractionSource


class ExtractionPipeline:
    """Main extraction pipeline: OCR → Rule → LLM → Validation → Scoring"""
    
    def __init__(self, use_llm: bool = False):
        self.validator = DataValidator()
        self.scorer = ConfidenceScorer()
        self.use_llm = use_llm
        self.llm_extractor = None
        
        if use_llm:
            try:
                self.llm_extractor = LLMExtractor()
            except ValueError as e:
                print(f"Warning: {str(e)}")
                print("LLM extraction disabled. Using rule-based extraction only.")
                self.use_llm = False
    
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
            # Step 1: Extract text using OCR (PaddleOCR)
            raw_text = extract_text_from_pdf(pdf_path)
            
            # Step 2: Extract using rules
            extracted_data = RuleBasedExtractor.extract_all(raw_text, document_type)
            
            # Step 3: Extract using LLM if enabled
            if self.use_llm and self.llm_extractor:
                try:
                    llm_data = self.llm_extractor.extract_from_text(raw_text, document_type)
                    extracted_data = self.llm_extractor.merge_extractions(extracted_data, llm_data)
                except Exception as e:
                    print(f"LLM extraction failed: {str(e)}, using rule-based only")
            
            # Step 4: Validate and clean extracted data
            validated_fields = self._validate_extracted_data(extracted_data)
            
            # Step 5: Calculate confidence scores
            overall_confidence = self.scorer.score_extraction_quality(validated_fields)
            
            # Build final result
            result = DocumentExtraction(
                document_name=Path(pdf_path).name,
                extracted_fields=validated_fields,
                overall_confidence=round(overall_confidence, 2),
                raw_text=raw_text[:1000],  # First 1000 chars
                page_count=self._get_page_count(pdf_path),
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
        """Validate and convert extracted data"""
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
    
    def _validate_field(self, field_name: str, value) -> tuple:
        """Validate individual field based on type"""
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
        """Return the number of pages in a PDF."""
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                return len(pdf.pages)
        except Exception:
            pass

        try:
            from pdf2image import pdfinfo_from_path
            return int(pdfinfo_from_path(pdf_path).get("Pages", 1))
        except Exception:
            return 1
