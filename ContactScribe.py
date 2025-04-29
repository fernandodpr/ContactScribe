import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os

CSV_PATH = "contactos.csv"
PDF_PATH = "contactos_exportados.pdf"

# Cargar CSV y limpiar
df = pd.read_csv(CSV_PATH, dtype=str).fillna("")
df["Nombre completo"] = df["Nombre"].str.strip() + " " + df["Apellidos"].str.strip()
df = df.sort_values("Nombre completo")

# Crear PDF
c = canvas.Canvas(PDF_PATH, pagesize=A4)
width, height = A4
y = height - 40

# Fecha de exportación
fecha_exportacion = datetime.now().strftime("%d/%m/%Y")
c.setFont("Helvetica-Oblique", 10)
c.drawString(40, y, f"Export date: {fecha_exportacion}")
y -= 30

# Configuración de columnas
telefonos = {
    "Teléfono (Trabajo)": "(trabajo)",
    "Teléfono particular": "(personal)",
    "Teléfono móvil": "(móvil)"
}
emails = [
    "Dirección de correo electrónico principal",
    "Dirección de correo electrónico secundaria"
]
direcciones_personal = [
    "Dirección personal", "Dirección personal 2", "Ciudad donde vive", "Provincia",
    "Código postal", "País de residencia"
]
direcciones_trabajo = [
    "Dirección de trabajo", "Dirección de trabajo 2", "Ciudad (Trabajo)",
    "Provincia (Trabajo)", "Código postal (Trabajo)", "País (Trabajo)"
]
nombres_extra = ["Nombre mostrado", "Apodo"]

campos_ignorados = [
    "Nombre completo", "Nombre", "Apellidos", *telefonos.keys(), *emails,
    *direcciones_personal, *direcciones_trabajo, "Puesto", "Departamento", "Organización",
    "Página web 1", "Página web 2", "Año de nacimiento", "Mes de nacimiento", "Día de nacimiento"
]

# Recorremos contactos
for _, row in df.iterrows():
    if y < 100:
        c.showPage()
        y = height - 40

    # Mostrar todos los nombres
    c.setFont("Helvetica-Bold", 12)
    nombre_base = f"{row['Nombre']} {row['Apellidos']}".strip()
    c.drawString(40, y, nombre_base)
    y -= 15

    c.setFont("Helvetica", 10)
    for campo in nombres_extra:
        if row[campo]:
            c.drawString(40, y, f"{campo}: {row[campo]}")
            y -= 12

    # Teléfonos
    tel_str = [f"{row[campo]} {etiqueta}" for campo, etiqueta in telefonos.items() if row[campo]]
    if tel_str:
        c.drawString(40, y, "Phones: " + ", ".join(tel_str))
        y -= 12

    # Emails
    email_str = [row[e] for e in emails if row[e]]
    if email_str:
        c.drawString(40, y, "Emails: " + ", ".join(email_str))
        y -= 12

    # Direcciones
    dir_pers = ", ".join([row[col] for col in direcciones_personal if row[col]])
    if dir_pers:
        c.drawString(40, y, f"Home: {dir_pers}")
        y -= 12
    dir_trab = ", ".join([row[col] for col in direcciones_trabajo if row[col]])
    if dir_trab:
        c.drawString(40, y, f"Work: {dir_trab}")
        y -= 12

    # Info laboral
    puesto = row["Puesto"]
    telefono_trab = row["Teléfono (Trabajo)"]
    correo_trab = row["Dirección de correo electrónico principal"]
    if puesto or telefono_trab or correo_trab:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, puesto)
        y -= 12
        c.setFont("Helvetica", 10)
        if telefono_trab:
            c.drawString(40, y, f"Work phone: {telefono_trab}")
            y -= 12
        if correo_trab:
            c.drawString(40, y, f"Work email: {correo_trab}")
            y -= 12

    # Fecha de nacimiento
    if all(row[col] for col in ["Día de nacimiento", "Mes de nacimiento", "Año de nacimiento"]):
        try:
            fecha_nac = f"{int(row['Día de nacimiento']):02}/{int(row['Mes de nacimiento']):02}/{row['Año de nacimiento']}"
            c.drawString(40, y, f"Birthdate: {fecha_nac}")
            y -= 12
        except ValueError:
            pass

    # Otros campos
    otros = [f"{row[col]}" for col in df.columns if col not in campos_ignorados and row[col]]
    if otros:
        c.drawString(40, y, "Other: " + ", ".join(otros))
        y -= 12

    # Línea divisoria
    c.line(40, y, width - 40, y)
    y -= 20

# Guardar PDF
c.save()
print(f"PDF generado en: {os.path.abspath(PDF_PATH)}")
