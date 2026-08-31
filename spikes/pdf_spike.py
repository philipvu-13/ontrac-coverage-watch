import pdfplumber

PDF = "out/ontrac-zip-2026.pdf"

with pdfplumber.open(PDF) as pdf:
    for i, page in enumerate(pdf.pages, start=1):
        lines = (page.extract_text() or "").splitlines()
        header = lines[1] if len(lines) > 1 else ""
        footer = lines[-1] if lines else ""
        print("{:>3}  {}  |  {}".format(i, header, footer))