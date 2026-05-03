from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


class ExtractionSource(str, Enum):
    RULE = "rule"
    LLM = "llm"
    HYBRID = "hybrid"


class ExtractedField(BaseModel):
    """Single extracted field with metadata"""
    name: str
    value: Any
    confidence: float = Field(..., ge=0, le=1)
    source: ExtractionSource = ExtractionSource.RULE
    raw_text: Optional[str] = None


class DocumentExtraction(BaseModel):
    """Complete document extraction result"""
    document_name: str
    extracted_fields: Dict[str, ExtractedField]
    overall_confidence: float = Field(..., ge=0, le=1)
    raw_text: str
    page_count: int
    processing_time: float  # in seconds
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_name": "invoice.pdf",
                "extracted_fields": {
                    "invoice_number": {
                        "name": "invoice_number",
                        "value": "INV-2024-001",
                        "confidence": 0.95,
                        "source": "rule"
                    }
                },
                "overall_confidence": 0.92,
                "raw_text": "...",
                "page_count": 1,
                "processing_time": 2.5,
                "error": None
            }
        }


class ExtractionRequest(BaseModel):
    """API request for document extraction"""
    document_type: str = Field(default="invoice", description="Type of document to extract")
    include_raw_text: bool = Field(default=False, description="Include raw OCR text in response")


class ExtractionResponse(BaseModel):
    """API response for document extraction"""
    success: bool
    data: Optional[DocumentExtraction] = None
    error: Optional[str] = None
    message: str
