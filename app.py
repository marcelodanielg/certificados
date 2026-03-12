import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io
import os

# --- ESTÉTICA DE LA INTERFAZ ---
st.set_page_config(page_title="Certificación Oficial", page_icon="🎓", layout="centered")

# CSS para eliminar marcas de agua y dejar la interfaz sobria
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    #stDecoration {display:none;}
    .stDeployButton {display:none;}
    [data-testid="stStatusWidget"] {visibility: hidden;}
    .stApp { background-color: #ffffff; }
    .stButton>button {
        background-color: #000000;
        color: #ffffff;
        border-radius: 2px;
        border: none;
        padding: 0.6rem 2rem;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def cargar_datos():
    if not os.path.exists("asistentes.xlsx"):
        return None
    try:
        df = pd.read_excel("asistentes.xlsx", dtype={'DNI': str})
        df['DNI'] = df['DNI'].str.strip()
        df['Nombre'] = df['Nombre'].str.strip()
        return df
    except:
        return None

# --- PANEL DE CONFIGURACIÓN PRIVADO ---
st.sidebar.markdown("### 🔒 Administración")
clave = st.sidebar.text_input("Contraseña de ajuste", type="password")

# Valores por defecto (se usan si no entras al modo admin)
if clave == "admin2026": # <--- Tu contraseña
    st.sidebar.success("Modo Configuración")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Texto (Nombre - DNI)")
    txt_x = st.sidebar.slider("Posición X Texto", 0, 5000, 2351)
    txt_y = st.sidebar.slider("Posición Y Texto", 0, 5000, 850)
    txt_size = st.sidebar.slider("Tamaño Texto", 10, 300, 95)
    txt_font = st.sidebar.selectbox("Tipo de Letra", ["Helvetica-Bold", "Helvetica", "Times-Bold", "Times-Roman", "Courier-Bold"])

    st.sidebar.markdown("---")
    st.sidebar.subheader("Código QR")
    qr_x = st.sidebar.slider("Posición X QR", 0, 5000, 4200)
    qr_y = st.sidebar.slider("Posición Y QR", 0, 5000, 2800)
    qr_size = st.sidebar.slider("Tamaño QR", 100, 1000, 350)
else:
    # Estos valores se aplicarán a los 30,000 docentes
    txt_x, txt_y, txt_size, txt_font = 2351, 850, 95, "Helvetica-Bold"
    qr_x, qr_y, qr_size = 4200, 2800, 350

LINK_APP = "https://certificados-9fnndcn82jqmyappo29hipd.streamlit.app/"

# --- GENERACIÓN DE PDF ---
def generar_pdf(nombre, dni):
    url = f"{LINK_APP}?validar={dni}"
    qr = qrcode.make(url)
    qr_buf = io.BytesIO()
    qr.save(qr_buf, format='PNG')
    qr_buf.seek(0)

    buffer = io.BytesIO()
    try:
        plantilla = Image.open("plantilla.png")
    except:
        st.error("Error: No se encontró 'plantilla.png'")
        return None
        
    ancho, alto = plantilla.size
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))
    c.drawImage("plantilla.png", 0, 0, width=ancho, height=alto)
    
    # Dibujar Texto Configurado
    c.setFont(txt_font, txt_size)
    c.drawCentredString(txt_x, alto - txt_y, f"{nombre.upper()} - DNI: {dni}")
    
    # Dibujar QR Configurado
    c.drawImage(ImageReader(qr_buf), qr_x, alto - qr_y, width=qr_size, height=qr_size)
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- NAVEGACIÓN Y PANTALLAS ---
df = cargar_datos()
query = st.query_params

if query.get("validar"):
    dni_v = query.get("validar")
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    if df is not None:
        doc = df[df['DNI'] == dni_v]
        if not doc.empty:
            st.markdown(f"""
                <div style="text-align: center; border: 1px solid #eee; padding: 50px; border-radius: 4px; font-family: sans-serif;">
                    <p style="text-transform: uppercase; letter-spacing: 3px; color: #999; font-size: 10px;">Verificación Oficial</p>
                    <h2 style="color: #2c5e2e; font-weight: 300;">✓ Documento Válido</h2>
                    <h1 style="font-weight: 600; font-size: 28px; color: #1a1a1a;">{doc.iloc[0]['Nombre']}</h1>
                    <p style="color: #666;">DNI {dni_v}</p>
                </div>
            """, unsafe_allow_html=True)
    st.stop()

# PANTALLA DE USUARIO
st.markdown("<br><br><br>",
