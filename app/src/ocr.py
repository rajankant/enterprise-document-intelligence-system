import os
import tempfile
from pathlib import Path
from typing import List, Tuple

ocr = None


def _get_ocr():
    """Initialize PaddleOCR only when OCR is actually used."""
    global ocr
    if ocr is None:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise ImportError(
                "PaddleOCR is not installed. Run `pip install -r requirements.txt` "
                "from the project root before processing PDFs."
            ) from exc
        ocr = PaddleOCR(use_angle_cls=True, lang='en')
    return ocr


def _convert_from_path(pdf_path: str):
    try:
        from pdf2image import convert_from_path
    except ImportError as exc:
        raise ImportError(
            "pdf2image is not installed. Run `pip install -r requirements.txt` "
            "from the project root before processing PDFs."
        ) from exc
    return convert_from_path(pdf_path)


def _extract_text_with_pdfplumber(pdf_path: str) -> str:
    try:
        import pdfplumber
    except ImportError:
        return ""

    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            if text.strip():
                pages_text.append(f"\n--- Page {page_num} ---\n{text}")

    return "".join(pages_text)


def extract_text_from_pdf(pdf_path: str, use_gpu: bool = False) -> str:
    """
    Extract text from PDF using embedded text first, then PaddleOCR.
    
    Args:
        pdf_path: Path to PDF file
        use_gpu: Whether to use GPU (requires CUDA)
        
    Returns:
        Extracted text from all pages
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    try:
        embedded_text = _extract_text_with_pdfplumber(pdf_path)
        if embedded_text.strip():
            return embedded_text

        # Convert PDF to images
        images = _convert_from_path(pdf_path)
        all_text = ""
        
        ocr_engine = _get_ocr()
        temp_dir = Path(tempfile.gettempdir())

        for page_num, image in enumerate(images, 1):
            # Save image temporarily
            temp_image_path = str(temp_dir / f"page_{page_num}.png")
            image.save(temp_image_path)
            
            try:
                # Extract text using PaddleOCR
                result = ocr_engine.ocr(temp_image_path, cls=True)
                
                # Combine text from all detected regions
                page_text = ""
                for line in result:
                    if line:
                        for word_info in line:
                            text = word_info[1][0]
                            confidence = word_info[1][1]
                            if confidence > 0.3:  # Filter low confidence
                                page_text += text + " "
                
                all_text += f"\n--- Page {page_num} ---\n{page_text}"
            
            finally:
                # Clean up temp image
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
        
        return all_text
    
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")


def extract_text_with_confidence(pdf_path: str) -> List[Tuple[str, float]]:
    """
    Extract text with confidence scores
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        List of (text, confidence) tuples
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    try:
        images = _convert_from_path(pdf_path)
        results = []
        
        ocr_engine = _get_ocr()
        temp_dir = Path(tempfile.gettempdir())

        for page_num, image in enumerate(images, 1):
            temp_image_path = str(temp_dir / f"page_{page_num}.png")
            image.save(temp_image_path)
            
            try:
                result = ocr_engine.ocr(temp_image_path, cls=True)
                
                for line in result:
                    if line:
                        for word_info in line:
                            text = word_info[1][0]
                            confidence = word_info[1][1]
                            results.append((text, confidence))
            
            finally:
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
        
        return results
    
    except Exception as e:
        raise Exception(f"Error extracting text with confidence: {str(e)}")


if __name__ == "__main__":
    # Test extraction
    pdf_path = r"C:\Users\kashy\Projects\AI Projects\ai-document-intelligence\enterprise-document-intelligence-system\app\input\JD-AIPython (1).pdf"
    
    extracted_text = extract_text_from_pdf(pdf_path)
    print("Extracted Text:")
    print(extracted_text[:500])  # Print first 500 chars
    print("\n...")
