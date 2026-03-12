import streamlit as st
import pandas as pd
import qrcode
import io
import os
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# --- ESTÉTICA SOBRIA ---
st.set_page_config(page_title="Gestor Institucional", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("asistentes.xlsx", dtype={'DNI': str})
        return df
    except:
        return None

df = cargar_datos()

# --- PANEL DE CONTROL (SOLO PARA TI) ---
st.sidebar.title("🛠 Ajuste de Plantilla")
clave = st.sidebar.text_input("Contraseña Administrador", type="password")

if clave == "admin2026":
    st.sidebar.success("Modo Edición Activado")
    
    st.sidebar.subheader("Posición Nombre y DNI")
    txt_x = st.sidebar.slider("Horizontal (X)", 0, 5000, 2350, step=10)
    txt_y = st.sidebar.slider("Vertical (Y)", 0, 5000, 850, step=10)
    txt_size = st.sidebar.slider("Tamaño Letra", 10, 200, 90)
    txt_font = st.sidebar.selectbox("Fuente", ["Helvetica-Bold", "Times-Bold", "Courier-Bold"])

    st.sidebar.subheader("Posición Código QR")
    qr_x = st.sidebar.slider("Horizontal QR", 0, 5000, 4200, step=10)
    qr_y = st.sidebar.slider("Vertical QR", 0, 5000, 2800, step=10)
    qr_size = st.sidebar.slider("Tamaño del QR", 100, 800, 350)
    
    mostrar_previa = True
else:
    # Estos valores se guardan solos cuando dejas de ser admin
    txt_x, txt_y, txt_size, txt_font = 2350, 850, 90, "Helvetica-Bold"
    qr_x, qr_y, qr_size = 4200, 2800, 350
    mostrar_previa = False

# --- FUNCIÓN DE VISTA PREVIA (IMAGEN) ---
def generar_vista_previa(nombre, dni):
    img = Image.open("plantilla.png").convert("RGB")
    ancho, alto = img.size
    draw = ImageDraw.Draw(img)
    
    # Simular texto (usamos fuente por defecto para la previa rápida)
    try:
        # Intentar cargar una fuente, si no usar la básica
        fnt = ImageFont.truetype("arial.ttf", txt_size)
    except:
        fnt = ImageFont.load_default()
        
    texto = f"{nombre.upper()} - DNI: {dni}"
    draw.text((txt_x, txt_y), texto, font=fnt, fill=(0,0,0), anchor="mm")
    
    # Simular QR (cuadrado negro)
    draw.rectangle([qr_x, qr_y, qr_x + qr_size, qr_y + qr_size], fill="black")
    
    img.thumbnail((1000, 1000)) # Achicar para que cargue rápido
    return img

# --- FUNCIÓN PDF ---
def generar_pdf(nombre, dni):
    buffer = io.BytesIO()
    plantilla = Image.open("plantilla.png")
    ancho, alto = plantilla.size
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))
    c.drawImage("plantilla.png", 0, 0, width=ancho, height=alto)
    
    # Texto
    c.setFont(txt_font, txt_size)
    c.drawCentredString(txt_x, alto - txt_y, f"{nombre.upper()} - DNI: {dni}")
    
    # QR
    url_v = f"https://tu-app.streamlit.app/?validar={dni}"
    qr = qrcode.make(url_v)
    qr_buf = io.BytesIO()
    qr.save(qr_buf, format='PNG')
    qr_buf.seek(0)
    c.drawImage(ImageReader(qr_buf), qr_x, alto - (qr_y + qr_size), width=qr_size, height=qr_size)
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- INTERFAZ DOCENTE ---
st.markdown("<h2 style='text-align: center; font-weight: 300;'>Portal de Certificación</h2>", unsafe_allow_html=True)

# Si eres admin, te muestra la previa para que ubiques los elementos
if mostrar_previa:
    st.info("💡 Mueve los sliders de la izquierda para ubicar el Nombre y el QR. Esta vista es solo para ti.")
    img_v = generar_vista_previa("JUAN PEREZ", "12345678")
    st.image(img_v, caption="Previsualización de diseño")

dni_input = st.text_input("Ingrese su DNI", placeholder="Ej: 12345678")

if dni_input and df is not None:
    res = df[df['DNI'].astype(str) == dni_input]
    if not res.empty:
        nombre_doc = res.iloc[0]['Nombre']
        st.success(f"Certificado listo para {nombre_doc}")
        pdf = generar_pdf(nombre_doc, dni_input)
        st.download_button("⬇️ DESCARGAR CERTIFICADO PDF", data=pdf, file_name=f"Certificado_{dni_input}.pdf")
    else:
        st.error("DNI no encontrado.")
