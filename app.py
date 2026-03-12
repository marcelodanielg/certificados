import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io

# --- CONFIGURACIÓN DE ESTÉTICA ---
st.set_page_config(page_title="Sistema Oficial de Certificación", page_icon="🎓", layout="centered")

# CSS para eliminar marcas de Streamlit y aplicar un estilo sobrio
style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {
        background-color: #ffffff;
    }
    .stButton>button {
        background-color: #1a1a1a;
        color: #ffffff;
        border-radius: 4px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: 300;
    }
    .stButton>button:hover {
        background-color: #333333;
        color: #ffffff;
    }
    input {
        border-radius: 4px !important;
    }
    </style>
    """
st.markdown(style, unsafe_allow_html=True)

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("asistentes.xlsx", dtype={'DNI': str})
        df['DNI'] = df['DNI'].str.strip()
        df['Nombre'] = df['Nombre'].str.strip()
        return df
    except:
        return None

df = cargar_datos()

# --- PANEL DE CONTROL PRIVADO (Solo Admin) ---
with st.sidebar:
    st.markdown("### 🔐 Configuración")
    pwd = st.text_input("Acceso", type="password")
    
    # Valores predeterminados (Edítalos aquí una vez configurados)
    if pwd == "admin2026": 
        st.success("Acceso concedido")
        txt_x = st.slider("Eje X Texto", 0, 5000, 2351)
        txt_y = st.slider("Eje Y Texto", 0, 5000, 850)
        qr_x = st.slider("Eje X QR", 0, 5000, 4200)
        qr_y = st.slider("Eje Y QR", 0, 5000, 2800)
        txt_size = st.slider("Tamaño", 50, 200, 95)
    else:
        # Valores de producción
        txt_x, txt_y, qr_x, qr_y, txt_size = 2351, 850, 4200, 2800, 95

# --- LÓGICA DE GENERACIÓN ---
LINK_APP = "https://certificados-9fnndcn82jqmyappo29hipd.streamlit.app/"

def generar_pdf(nombre, dni):
    url = f"{LINK_APP}?validar={dni}"
    qr = qrcode.make(url)
    qr_buf = io.BytesIO()
    qr.save(qr_buf, format='PNG')
    qr_buf.seek(0)

    buffer = io.BytesIO()
    plantilla = Image.open("plantilla.png")
    ancho, alto = plantilla.size
    
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))
    c.drawImage("plantilla.png", 0, 0, width=ancho, height=alto)
    c.setFont("Helvetica-Bold", txt_size)
    c.drawCentredString(txt_x, alto - txt_y, f"{nombre.upper()} - DNI: {dni}")
    c.drawImage(ImageReader(qr_buf),
