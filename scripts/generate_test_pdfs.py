#!/usr/bin/env python3
"""Generate test PDF files for integration testing.

This script creates realistic German medical bill PDFs for testing purposes.
Run this script to regenerate test PDFs when needed.
"""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def create_valid_bill_pdf(output_path: Path):
    """Create a valid German medical bill PDF with realistic content."""
    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "Dr. med. Anna Müller")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, "Fachärztin für Allgemeinmedizin")
    c.drawString(50, height - 85, "Hauptstraße 123, 10115 Berlin")
    c.drawString(50, height - 100, "Tel: 030/12345678")

    # Patient info
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 140, "Rechnung")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 160, "Patient: Max Mustermann")
    c.drawString(50, height - 175, "Rechnungsnummer: 2024-001234")
    c.drawString(50, height - 190, "Rechnungsdatum: 15.03.2024")

    # Services
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, height - 220, "Erbrachte Leistungen:")
    c.setFont("Helvetica", 9)

    y = height - 245
    c.drawString(50, y, "GOÄ-Ziffer 1")
    c.drawString(200, y, "Beratung")
    c.drawString(400, y, "10,72 EUR")

    y -= 20
    c.drawString(50, y, "GOÄ-Ziffer 5")
    c.drawString(200, y, "Untersuchung")
    c.drawString(400, y, "14,57 EUR")

    y -= 20
    c.drawString(50, y, "GOÄ-Ziffer 250")
    c.drawString(200, y, "Blutentnahme")
    c.drawString(400, y, "4,20 EUR")

    # Total
    c.line(50, y - 10, width - 50, y - 10)
    y -= 30
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Gesamtbetrag:")
    c.drawString(400, y, "29,49 EUR")

    # Footer
    c.setFont("Helvetica", 8)
    c.drawString(50, 50, "Bitte überweisen Sie den Betrag innerhalb von 14 Tagen.")
    c.drawString(50, 35, "Bankverbindung: IBAN DE12 3456 7890 1234 5678 90")

    c.save()
    print(f"✓ Created: {output_path.name}")


def create_multipage_bill_pdf(output_path: Path):
    """Create a multi-page German medical bill PDF."""
    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4

    # Page 1
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "Praxis Dr. Thomas Schmidt")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, "Zahnarztpraxis")
    c.drawString(50, height - 85, "Berliner Str. 456, 80331 München")

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 120, "Rechnung - Seite 1 von 2")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 140, "Patient: Maria Beispiel")
    c.drawString(50, height - 155, "Rechnungsnummer: 2024-005678")
    c.drawString(50, height - 170, "Rechnungsdatum: 22.06.2024")

    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, height - 200, "Erbrachte Leistungen (Seite 1):")
    c.setFont("Helvetica", 9)

    y = height - 225
    for i in range(1, 16):
        c.drawString(50, y, f"GOÄ {i}")
        c.drawString(200, y, f"Leistung {i}")
        c.drawString(400, y, f"{15 + i * 2:.2f} EUR")
        y -= 20
        if y < 100:
            break

    c.drawString(50, 70, "Fortsetzung auf Seite 2")
    c.showPage()

    # Page 2
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 50, "Rechnung - Seite 2 von 2")
    c.setFont("Helvetica", 9)

    y = height - 80
    for i in range(16, 25):
        c.drawString(50, y, f"GOÄ {i}")
        c.drawString(200, y, f"Leistung {i}")
        c.drawString(400, y, f"{15 + i * 2:.2f} EUR")
        y -= 20

    c.line(50, y - 10, width - 50, y - 10)
    y -= 30
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Gesamtbetrag:")
    c.drawString(400, y, "734,00 EUR")

    c.setFont("Helvetica", 8)
    c.drawString(50, 50, "Zahlbar innerhalb von 30 Tagen.")

    c.save()
    print(f"✓ Created: {output_path.name}")


def create_minimal_text_pdf(output_path: Path):
    """Create a PDF with very minimal text (simulates scanned detection)."""
    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4

    # Only 20 characters - below MIN_TEXT_LENGTH threshold of 50
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 50, "Dr. Minimal Text")

    c.save()
    print(f"✓ Created: {output_path.name} (minimal text, triggers scanned detection)")


def create_empty_pdf(output_path: Path):
    """Create a PDF with no text at all."""
    c = canvas.Canvas(str(output_path), pagesize=A4)
    # Don't draw any text, but show the page
    c.showPage()  # Add this to properly create a page
    c.save()
    print(f"✓ Created: {output_path.name} (no text)")


def main():
    """Generate all test PDFs."""
    script_dir = Path(__file__).parent
    test_data_dir = script_dir.parent / "tests" / "test_data" / "sample_bills"

    # Ensure directory exists
    test_data_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nGenerating test PDFs in: {test_data_dir}\n")

    # Create test PDFs
    create_valid_bill_pdf(test_data_dir / "valid_bill.pdf")
    create_multipage_bill_pdf(test_data_dir / "multipage_bill.pdf")
    create_minimal_text_pdf(test_data_dir / "minimal_text.pdf")
    create_empty_pdf(test_data_dir / "empty_text.pdf")

    print(f"\n✓ All test PDFs generated successfully!")
    print(f"\nNote: True scanned/image PDFs cannot be generated programmatically.")
    print(f"      The 'minimal_text.pdf' simulates scanned detection by having < 50 characters.")


if __name__ == "__main__":
    main()
