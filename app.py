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

# --- COORDENADAS Y ESTILO ---
# Ajustamos Y a un valor más alto para que suba a la primera cuarta parte
# Ajustamos X para que el conjunto nombre + dni quede estético
Y_SUPERIOR = 2200  # Ajusta este valor si queda muy arriba o muy abajo
TAMANO_FUENTE = 90

# --- FUNCIÓN GENERAR PDF ---
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
    
    # En ReportLab, la coordenada Y=0 es el borde INFERIOR. 
    # Para la cuarta parte superior de una imagen de alto ~3500, usamos ~2600.
    pos_y_pdf = alto * 0.75 

    c = canvas.Canvas(buffer, pagesize=(ancho, alto))
    c.drawImage("plantilla.png", 0, 0, width=ancho, height=alto)
    
    # Texto en el mismo renglón y mismo formato
    texto_completo = f"{nombre.upper()} - DNI: {dni}"
    
    c.setFont("Helvetica-Bold", TAMANO_FUENTE)
    c.drawCentredString(ancho / 2, pos_y_pdf, texto_completo)
    
    # Dibujar QR pequeño abajo
    c.drawImage(ImageReader(qr_img), ancho - 500, 100, width=300, height=300)
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- FUNCIÓN VISTA PREVIA ---
def generar_previsualizacion(nombre, dni):
    img = Image.open("plantilla.png").convert("RGB")
    ancho, alto = img.size
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", TAMANO_FUENTE)
    except:
        font = ImageFont.load_default()
    
    # En PIL (imagen), Y=0 es ARRIBA. La cuarta parte superior es alto * 0.25
    pos_y_img = alto * 0.25
    
    texto_completo = f"{nombre.upper()} - DNI: {dni}"
    
    # Centrar texto
    draw.text((ancho / 2, pos_y_img), texto_completo, font=font, fill=(0,0,0), anchor="mm")
    
    img.thumbnail((1000, 1000)) 
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- INTERFAZ ---
st.title("🎓 Generador de Certificados")

dni_input = st.text_input("Ingresa tu DNI:")

if dni_input and df is not None:
    res = df[df['DNI'] == dni_input]
    if not res.empty:
        nombre = res.iloc[0]['Nombre']
        
        # Vista previa
        img_preview = generar_previsualizacion(nombre, dni_input)
        st.image(img_preview, caption="Vista previa del renglón superior", use_container_width=True)
        
        # Descarga
        pdf_file = generar_pdf(nombre, dni_input)
        st.download_button(
            label="⬇️ Descargar PDF Oficial",
            data=pdf_file,
            file_name=f"Certificado_{dni_input}.pdf",
            mime="application/pdf"
        )
    else:
        st.error("DNI no encontrado.")
