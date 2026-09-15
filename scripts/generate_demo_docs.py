from pathlib import Path
from reportlab.pdfgen import canvas


def create_demo_pdf(path: Path, title: str, lines: list[str]):
    c = canvas.Canvas(str(path))
    c.setTitle(title)
    c.setFont("Helvetica", 18)
    c.drawString(72, 760, title)
    c.setFont("Helvetica", 12)
    y = 720
    for line in lines:
        c.drawString(72, y, line)
        y -= 20
    c.save()


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parents[1] / "app" / "input"
    base_dir.mkdir(parents=True, exist_ok=True)

    docs = [
        (
            "dummy_invoice.pdf",
            "Invoice Demo",
            [
                "Invoice Number: INV-1001",
                "Vendor: Northwind Traders",
                "Total Amount: $1,250.00",
                "Due Date: 2026-09-30",
            ],
        ),
        (
            "dummy_receipt.pdf",
            "Receipt Demo",
            [
                "Receipt ID: RCP-203",
                "Store: City Market",
                "Total Paid: $89.95",
                "Date: 2026-09-15",
            ],
        ),
    ]

    for name, title, lines in docs:
        create_demo_pdf(base_dir / name, title, lines)

    print("Created demo documents:")
    for path in sorted(base_dir.glob("*.pdf")):
        print(path.name)
