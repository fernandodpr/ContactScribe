import pandas as pd
import vobject
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from datetime import datetime
import os
import sys

def process_csv(file_path):
    df = pd.read_csv(file_path, dtype=str).fillna("")
    df["Nombre"] = df.get("Nombre", "")
    df["Apellidos"] = df.get("Apellidos", "")
    df = df.sort_values(["Nombre", "Apellidos"])
    return df

def process_vcf(file_path):
    contacts = []
    with open(file_path, "r", encoding="utf-8") as f:
        vcard_data = f.read()
    for vcard in vobject.readComponents(vcard_data):
        contact = {}
        # Name
        try:
            contact["Nombre"] = getattr(vcard.n.value, 'given', "")
            contact["Apellidos"] = getattr(vcard.n.value, 'family', "")
        except AttributeError:
            contact["Nombre"] = vcard.fn.value if hasattr(vcard, 'fn') else ""
            contact["Apellidos"] = ""
        # Full name
        if hasattr(vcard, "fn"):
            contact["Nombre mostrado"] = vcard.fn.value
        # Phones
        for tel in vcard.contents.get("tel", []):
            label = ", ".join(tel.params.get("TYPE", []))
            contact[f"Teléfono ({label})"] = tel.value
        # Emails
        for email in vcard.contents.get("email", []):
            label = ", ".join(email.params.get("TYPE", []))
            contact[f"Correo ({label})"] = email.value
        # Addresses
        for adr in vcard.contents.get("adr", []):
            label = ", ".join(adr.params.get("TYPE", []))
            adr_value = adr.value
            address = ", ".join(filter(None, [
                adr_value.street, adr_value.city, adr_value.region,
                adr_value.code, adr_value.country
            ]))
            contact[f"Dirección ({label})"] = address
        # Organization
        if hasattr(vcard, "org"):
            contact["Organización"] = ", ".join(vcard.org.value)
        # Title
        if hasattr(vcard, "title"):
            contact["Puesto"] = vcard.title.value
        # Notes
        if hasattr(vcard, "note"):
            contact["Notas"] = vcard.note.value
        contacts.append(contact)
    return pd.DataFrame(contacts).fillna("").sort_values(["Nombre", "Apellidos"])

def generate_pdf(df, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    y = height - 40

    export_date = datetime.now().strftime("%d/%m/%Y")
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(40, y, f"Export date: {export_date}")
    y -= 30

    for _, row in df.iterrows():
        if y < 100:
            c.showPage()
            y = height - 40

        # Name in bold
        full_name = f"{row.get('Nombre', '')} {row.get('Apellidos', '')}".strip()
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, full_name)
        y -= 15

        c.setFont("Helvetica", 10)
        for col in df.columns:
            if col in ("Nombre", "Apellidos"):
                continue
            value = row.get(col, "").strip()
            if value:
                lines = simpleSplit(f"{col}: {value}", "Helvetica", 10, width - 80)
                for line in lines:
                    c.drawString(40, y, line)
                    y -= 12

        c.line(40, y, width - 40, y)
        y -= 20

    c.save()
    print(f"PDF generated at: {os.path.abspath(output_path)}")

# Main
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ContactScribe.py <path_to_file.csv|vcf>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_pdf = os.path.splitext(input_path)[0] + ".pdf"

    ext = os.path.splitext(input_path)[1].lower()
    if ext == ".csv":
        df = process_csv(input_path)
    elif ext == ".vcf":
        df = process_vcf(input_path)
    else:
        print("Unsupported file format. Only .csv and .vcf are supported.")
        sys.exit(1)

    generate_pdf(df, output_pdf)
