import pandas as pd
import vobject
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from datetime import datetime
import os
import sys

# Translations for Spanish (Optional)
translations = {
    "es": {
        "Export date": "Fecha de exportación",
        "First Name": "Nombre",
        "Last Name": "Apellidos",
        "Display Name": "Nombre mostrado",
        "Phone": "Teléfono",
        "Email": "Correo",
        "Address": "Dirección",
        "Organization": "Organización",
        "Title": "Puesto",
        "Notes": "Notas",
        "Home": "Casa",
        "Work": "Trabajo",
        "Mobile": "Móvil",
        "Fax": "Fax",
        "Other": "Otro",
        "Internet": "Internet"
    },
    "en": {
        "Export date": "Export date",
        "First Name": "First Name",
        "Last Name": "Last Name",
        "Display Name": "Display Name",
        "Phone": "Phone",
        "Email": "Email",
        "Address": "Address",
        "Organization": "Organization",
        "Title": "Title",
        "Notes": "Notes",
        "Home": "Home",
        "Work": "Work",
        "Mobile": "Mobile",
        "Fax": "Fax",
        "Other": "Other",
        "Internet": "Internet"
    }
}

def translate(label, lang):
    # Translate compound field parts
    if "(" in label:
        base, tag = label.split("(", 1)
        tag = tag.rstrip(")")
        base_trans = translations.get(lang, {}).get(base.strip(), base.strip())
        tag_trans = ", ".join(translations.get(lang, {}).get(part.strip(), part.strip()) for part in tag.split(","))
        return f"{base_trans} ({tag_trans})"
    return translations.get(lang, {}).get(label.strip(), label.strip())

def process_csv(file_path):
    df = pd.read_csv(file_path, dtype=str).fillna("")
    df["First Name"] = df.get("First Name", "")
    df["Last Name"] = df.get("Last Name", "")
    df = df.sort_values(["First Name", "Last Name"])
    return df

def process_vcf(file_path):
    contacts = []
    with open(file_path, "r", encoding="utf-8") as f:
        vcard_data = f.read()
    for vcard in vobject.readComponents(vcard_data):
        contact = {}
        try:
            contact["First Name"] = getattr(vcard.n.value, 'given', "")
            contact["Last Name"] = getattr(vcard.n.value, 'family', "")
        except AttributeError:
            contact["First Name"] = vcard.fn.value if hasattr(vcard, 'fn') else ""
            contact["Last Name"] = ""
        if hasattr(vcard, "fn"):
            contact["Display Name"] = vcard.fn.value
        for tel in vcard.contents.get("tel", []):
            label = ", ".join(tel.params.get("TYPE", []))
            contact[f"Phone ({label})"] = tel.value
        for email in vcard.contents.get("email", []):
            label = ", ".join(email.params.get("TYPE", []))
            contact[f"Email ({label})"] = email.value
        for adr in vcard.contents.get("adr", []):
            label = ", ".join(adr.params.get("TYPE", []))
            adr_value = adr.value
            address = ", ".join(filter(None, [
                adr_value.street, adr_value.city, adr_value.region,
                adr_value.code, adr_value.country
            ]))
            contact[f"Address ({label})"] = address
        if hasattr(vcard, "org"):
            contact["Organization"] = ", ".join(vcard.org.value)
        if hasattr(vcard, "title"):
            contact["Title"] = vcard.title.value
        if hasattr(vcard, "note"):
            contact["Notes"] = vcard.note.value
        contacts.append(contact)
    return pd.DataFrame(contacts).fillna("").sort_values(["First Name", "Last Name"])

def generate_pdf(df, output_path, lang):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    y = height - 40

    export_date = datetime.now().strftime("%d/%m/%Y")
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(40, y, f"{translate('Export date', lang)}: {export_date}")
    y -= 30

    for _, row in df.iterrows():
        if y < 100:
            c.showPage()
            y = height - 40

        full_name = f"{row.get('First Name', '')} {row.get('Last Name', '')}".strip()
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, full_name)
        y -= 15

        c.setFont("Helvetica", 10)
        for col in df.columns:
            if col in ("First Name", "Last Name"):
                continue
            value = row.get(col, "").strip()
            if value:
                label = translate(col, lang)
                lines = simpleSplit(f"{label}: {value}", "Helvetica", 10, width - 80)
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
        print("Usage: python ContactScribe.py <path_to_file.csv|vcf> [lang]")
        sys.exit(1)

    input_path = sys.argv[1]
    lang = sys.argv[2] if len(sys.argv) > 2 else "en"  # Default language is set to 'en'
    if lang not in ("en", "es"):
        print("Unsupported language. Choose 'en' or 'es'.")
        sys.exit(1)

    output_pdf = os.path.splitext(input_path)[0] + ".pdf"

    ext = os.path.splitext(input_path)[1].lower()
    if ext == ".csv":
        df = process_csv(input_path)
    elif ext == ".vcf":
        df = process_vcf(input_path)
    else:
        print("Unsupported file format. Only .csv and .vcf are supported.")
        sys.exit(1)

    generate_pdf(df, output_pdf, lang)
