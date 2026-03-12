import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Generador Pro de Certificados", page_icon="🎓")

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

# --- BARRA LATERAL DE AJUSTES ---
st.sidebar.header("⚙️ Ajuste de Posición")
st.sidebar.info("Mueve los deslizadores para ubicar el texto en tu plantilla.")

# Obtenemos dimensiones de la plantilla para los límites de los sliders
img_temp = Image.open("plantilla.png")
ancho_ref, alto_ref = img_temp.size

pos_x = st.sidebar.slider("Posición Horizontal (X)", 0, ancho_ref, int(ancho_ref/2))
pos_y = st.sidebar.slider("Posición Vertical (Y)", 0, alto_ref, int(alto_ref*0.25))
tam_fuente = st.sidebar.slider("Tamaño de Letra", 20, 300, 90)

# URL para el QR (Asegúrate que sea la de tu app)
LINK_APP = "https://certificados-9fnndcn82jqmyappo29hipd.streamlit.app/"

# --- FUNCIONES DE GENERACIÓN ---

def crear_qr(dni):
    url = f"{LINK_APP}?validar={dni}"
    qr = qrcode.make(url)
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    buf.seek(0)
    return buf

def generar_pdf(nombre, dni, x, y, size):
    qr_buf = crear_qr(dni)
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(ancho_ref, alto_ref))
    
    # Dibujar Fondo
    c.drawImage("plantilla.png", 0, 0, width=ancho_ref, height=alto_ref)
    
    # Dibujar Texto (En PDF el 0 de Y es abajo, invertimos el valor del slider)
    y_pdf = alto_ref - y
    c.setFont("Helvetica-Bold", size)
    c.drawCentredString(x, y_pdf, f"{nombre.upper()} - DNI: {dni}")
    
    # Dibujar QR (Esquina inferior derecha por defecto)
    c.drawImage(ImageReader(qr_buf), ancho_ref - 550, 150, width=350, height=350)
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

def generar_vista_previa(nombre, dni, x, y, size):
    img = Image.open("plantilla.png").convert("RGB")
    draw = ImageDraw.Draw(img)
    
    # Dibujar Texto
    try:
        font = ImageFont.truetype("arial.ttf", size)
    except:
        font = ImageFont.load_default()
    
    texto = f"{nombre.upper()} - DNI: {dni}"
    draw.text((x, y), texto, font=font, fill=(0,0,0), anchor="mm")
    
    # Dibujar QR en la vista previa
    qr_buf = crear_qr(dni)
    qr_img = Image.open(qr_buf).resize((350, 350))
    img.paste(qr_img, (ancho_ref - 550, alto_ref - 500))
    
    # Redimensionar para que Streamlit lo muestre fluido
    img.thumbnail((1200, 1200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()

# --- LÓGICA DE LA APP ---

# 1. MODO VALIDADOR (Si escanean el QR)
query = st.query_params
if query.get("validar"):
    dni_v = query.get("validar")
    st.title("🔍 Validador Oficial")
    if df is not None:
        doc = df[df['DNI'] == dni_v]
        if not doc.empty:
            st.success(f"### ✅ AUTÉNTICO: {doc.iloc[0]['Nombre']}")
            st.balloons()
        else:
            st.error("### ❌ NO VÁLIDO")
    if st.button("Volver"):
        st.query_params.clear()
        st.rerun()
    st.stop()

# 2. MODO DESCARGA
st.title("🎓 Sistema de Certificación")

dni_input = st.text_input("Ingresa tu DNI para previsualizar:")

if dni_input and df is not None:
    res = df[df['DNI'] == dni_input]
    if not res.empty:
        nombre_doc = res.iloc[0]['Nombre']
        
        # Mostrar Vista Previa con los ajustes de los Sliders
        st.subheader("Vista Previa")
        previa = generar_vista_previa(nombre_doc, dni_input, pos_x, pos_y, tam_fuente)
        st.image(previa, use_container_width=True)
        
        # Botón para descargar el PDF final
        st.write("---")
        pdf_file = generar_pdf(nombre_doc, dni_input, pos_x, pos_y, tam_fuente)
        st.download_button(
            label="⬇️ Descargar PDF Final",
            data=pdf_file,
            file_name=f"Certificado_{dni_input}.pdf",
            mime="application/pdf"
        )
    else:
        st.error("DNI no encontrado.")
