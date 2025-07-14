from fpdf import FPDF

def text_to_pdf(text, filename="output.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    lines = text.split("\n")
    for line in lines:
        pdf.cell(200, 10, txt=line, ln=1, align="L")

    pdf.output(filename)
    return filename