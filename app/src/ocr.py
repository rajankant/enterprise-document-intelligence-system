import fitz

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

if __name__ == "__main__":
    pdf_path = r"C:\Users\kashy\Projects\AI Projects\ai-document-intelligence\enterprise-document-intelligence-system\app\input\JD-AIPython (1).pdf"  # Replace with your PDF file path
    extracted_text = extract_text_from_pdf(pdf_path)
    print(extracted_text)