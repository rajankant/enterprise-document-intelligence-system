from pathlib import Path

from rag.rag_service import RAGService


def test_rag_service_returns_relevant_chunks(tmp_path):
    sample_doc = tmp_path / "invoice_demo.txt"
    sample_doc.write_text(
        """
        Invoice Number: INV-1001
        Vendor: Northwind Traders
        Total Amount: $1,250.00
        Due Date: 2026-09-30
        """.strip(),
        encoding="utf-8",
    )

    service = RAGService()
    service.index_documents([str(sample_doc)])

    results = service.query("Who is the vendor for this invoice?")

    assert results
    assert any("Northwind Traders" in item["text"] for item in results)
    assert results[0]["score"] > 0
