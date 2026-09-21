from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

SAMPLE_TEXT = [
    "POSTANOVLENIE o vzyskanii",
    "Delo N 12345/2024",
    "Dolzhnik: Ivanov Ivan Ivanovich",
    "Summa dolga: 450 000 rub.",
    "Marka, model: Toyota Camry",
    "VIN: JTDBE32K123456789",
    "God vypuska: 2015",
    "Probeg: 180000 km",
    "Gos. nomer: A123BC777",
]


def make_pdf(lines: list[str] | None = None) -> bytes:
    """Генерит однотипный PDF для тестов (латиница — шрифты в CI не нужны)."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    y = 800
    for line in lines or SAMPLE_TEXT:
        pdf.drawString(50, y, line)
        y -= 20
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
