import streamlit as st
import pandas as pd
import qrcode
import io
import os
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# --- LIMPIEZA TOTAL DE INTERFAZ ---
st.set_page_config(page_title="Sistema de Certificación", page_icon="🎓", layout="centered")

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

# --- VERIFICACIÓN DE ARCHIVOS ---
def verificar_archivos():
    errores = []
    if not os.path.exists("asistentes.xlsx"): errores.append("Falta el archivo 'asistentes.xlsx'")
    if not os.path.exists("plantilla.png"): errores.append("Falta la imagen 'plantilla.png'")
    return errores

errores_archivos = verificar_archivos()
if errores_archivos:
    for e in errores_archivos: st.error(e)
    st.stop()

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    df = pd.read_excel("asistentes.xlsx", dtype={'DNI': str})
    df['DNI'] = df['DNI'].str.strip()
    df['Nombre'] = df['Nombre'].str.strip()
    return df

df = cargar_datos()

# --- PANEL DE CONTROL (ADMIN) ---
st.sidebar.markdown("### 🔒 Administración")
clave = st.sidebar.text_input("Contraseña", type="password")

# Ajustes de diseño
if clave == "admin2026": # Puedes cambiar esta clave
    st.sidebar.success("Modo Edición")
    txt_x = st.sidebar.slider("X Texto", 0, 5000, 2351)
    txt_y = st.sidebar.slider("Y Texto", 0, 5000, 850)
    txt_size = st.sidebar.slider("Tamaño Fuente", 10, 200, 95)
    txt_font = st.sidebar.selectbox("Fuente", ["Helvetica-Bold", "Times-Bold", "Courier-Bold"])
    qr_x = st.sidebar.slider("X QR", 0, 5000, 4200)
    qr_y = st.sidebar.slider("Y QR", 0, 5000, 2800)
    qr_size = st.sidebar.slider("Tamaño QR", 100, 1000, 350)
else:
    # Valores por defecto cuando no eres admin
    txt_x, txt_y, txt_size, txt_font = 2351, 850, 95, "Helvetica-Bold"
    qr_x, qr_y, qr_size = 4200, 2800, 350

LINK_APP = "https://certificados-9fnndcn82jqmyappo29hipd.streamlit.app/"

# --- GENERACIÓN DE PDF ---
def generar_pdf(nombre, dni):
    url_v = f"{LINK_APP}?validar={dni}"
    qr = qrcode.make(url_v)
    qr_buf = io.BytesIO()
    qr.save(qr_buf, format='PNG')
    qr_buf.seek(0)

    buffer = io.BytesIO()
    plantilla = Image.open("plantilla.png")
    ancho, alto = plantilla.size
    
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))
    c.drawImage("plantilla.png", 0, 0, width=ancho, height=alto)
    
    # Texto
    c.setFont(txt_font, txt_size)
    c.drawCentredString(txt_x, alto - txt_y, f"{nombre.upper()} - DNI: {dni}")
    
    # QR
    c.drawImage(ImageReader(qr_buf), qr_x, alto - qr_y, width=qr_size, height=qr_size)
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- LÓGICA DE PANTALLAS ---
query = st.query_params

if query.get("validar"):
    dni_v = query.get("validar")
    doc = df[df['DNI'] == dni_v]
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    if not doc.empty:
        st.markdown(f"""
            <div style="text-align: center; border: 1px solid #eee; padding: 50px; border-radius: 4px;">
                <p style="text-transform: uppercase; letter-spacing: 3px; color: #999; font-size: 10px;">Verificación Oficial</p>
                <h2 style="color: #2c5e2e; font-weight: 300;">✓ Documento Válido</h2>
                <h1 style="font-weight: 600; font-size: 28px; color: #1a1a1a;">{doc.iloc[0]['Nombre']}</h1>
                <p style="color: #666;">DNI {dni_v}</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.error("Documento no registrado.")
    st.stop()

# PANTALLA PRINCIPAL
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; font-weight: 300;'>Portal de Certificación</h2>", unsafe_allow_html=True)

dni_input = st.text_input("DNI", label_visibility="collapsed", placeholder="Ingrese su número de DNI")

if dni_input:
    res = df[df['DNI'] == dni_input]
    if not res.empty:
        nombre_doc = res.iloc[0]['Nombre']
        st.info(f"Certificado para: {nombre_doc}")
        pdf_file = generar_pdf(nombre_doc, dni_input)
        st.download_button("DESCARGAR PDF", data=pdf_file, file_name=f"Certificado_{dni_input}.pdf", mime="application/pdf")
    else:
        st.error("DNI no registrado.")
