import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Certificados Oficiales", page_icon="🎓")

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("asistentes.xlsx", dtype={'DNI': str})
        df['DNI'] = df['DNI'].str.strip()
        df['Nombre'] = df['Nombre'].str.strip()
        return df
    except Exception as e:
        st.error(f"Error al cargar Excel: {e}")
        return None

df = cargar_datos()

# --- FUNCIÓN GENERAR PDF (PARA DESCARGA) ---
def generar_pdf(nombre, dni):
    link_web = "https://certificados-9fnndcn82jqmyappo29hipd.streamlit.app/"
    url_validacion = f"{link_web}?dni_verificar={dni}"
    
    qr = qrcode.make(url_validacion)
    qr_img = io.BytesIO()
    qr.save(qr_img, format='PNG')
    qr_img.seek(0)

    buffer = io.BytesIO()
    plantilla = Image.open("plantilla.png")
    ancho, alto = plantilla.size
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))
    c.drawImage("plantilla.png", 0, 0, width=ancho, height=alto)
    
    c.setFont("Helvetica-Bold", 110)
    c.drawCentredString(2351, 1575, nombre.upper())
    c.setFont("Helvetica", 70)
    c.drawCentredString(4803, 1575, f"DNI: {dni}")
    c.drawImage(ImageReader(qr_img), ancho - 600, 150, width=400, height=400)
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- FUNCIÓN GENERAR IMAGEN (PARA VISTA PREVIA RÁPIDA) ---
def generar_previsualizacion(nombre, dni):
    img = Image.open("plantilla.png").convert("RGB")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 110)
    except:
        font = ImageFont.load_default()
    
    # Coordenadas idénticas a las del PDF
    draw.text((2351, 1575), nombre.upper(), font=font, fill=(0,0,0), anchor="mm")
    
    # Redimensionamos solo para la vista previa para que cargue instantáneo
    img.thumbnail((1000, 1000)) 
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- INTERFAZ ---
st.title("🎓 Descarga tu Certificado")

# Validador de QR
if st.query_params.get("dni_verificar"):
    dni_v = st.query_params.get("dni_verificar")
    if df is not None:
        if not df[df['DNI'] == dni_v].empty:
            st.success(f"✅ CERTIFICADO AUTÉNTICO: {df[df['DNI'] == dni_v].iloc[0]['Nombre']}")
            st.balloons()

dni_input = st.text_input("Ingresa tu DNI:")

if dni_input and df is not None:
    res = df[df['DNI'] == dni_input]
    if not res.empty:
        nombre = res.iloc[0]['Nombre']
        
        # 1. Mostrar Imagen de Vista Previa (Esto SIEMPRE se ve)
        img_preview = generar_previsualizacion(nombre, dni_input)
        st.image(img_preview, caption="Vista previa de tu certificado", use_container_width=True)
        
        # 2. Botón para el PDF Real
        pdf_file = generar_pdf(nombre, dni_input)
        st.download_button(
            label="⬇️ Descargar Certificado Oficial (PDF)",
            data=pdf_file,
            file_name=f"Certificado_{dni_input}.pdf",
            mime="application/pdf"
        )
    else:
        st.error("DNI no encontrado.")
