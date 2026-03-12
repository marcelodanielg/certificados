import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io

# --- CONFIGURACIÓN DE INTERFAZ ---
st.set_page_config(page_title="Sistema de Certificación Institucional", page_icon="🎓", layout="centered")

# CSS Avanzado para ocultar TODO (Menú, Footer, Marca de agua)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    #stDecoration {display:none;}
    .stDeployButton {display:none;}
    .stApp { background-color: #ffffff; }
    
    /* Botón elegante */
    .stButton>button {
        background-color: #000000;
        color: #ffffff;
        border-radius: 2px;
        border: none;
        padding: 0.6rem 2rem;
        font-weight: 400;
        letter-spacing: 1px;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #333333;
        color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def cargar_datos():
    if not os.path.exists("asistentes.xlsx"):
        st.error("Archivo 'asistentes.xlsx' no encontrado en el repositorio.")
        return None
    try:
        df = pd.read_excel("asistentes.xlsx", dtype={'DNI': str})
        df['DNI'] = df['DNI'].str.strip()
        return df
    except Exception as e:
        st.error(f"Error al leer Excel: {e}")
        return None

import os

# --- CONFIGURACIÓN ADMIN ---
# Estos valores son los que ajustaste previamente
LINK_APP = "https://certificados-9fnndcn82jqmyappo29hipd.streamlit.app/"
txt_x, txt_y, qr_x, qr_y, txt_size = 2351, 850, 4200, 2800, 95

# --- GENERACIÓN DE PDF ---
def generar_pdf(nombre, dni):
    if not os.path.exists("plantilla.png"):
        st.error("No se encontró 'plantilla.png'")
        return None
        
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
    
    # Texto
    c.setFont("Helvetica-Bold", txt_size)
    c.drawCentredString(txt_x, alto - txt_y, f"{nombre.upper()} - DNI: {dni}")
    
    # QR
    c.drawImage(ImageReader(qr_buf), qr_x, alto - qr_y, width=350, height=350)
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- NAVEGACIÓN ---
df = cargar_datos()
query = st.query_params

if query.get("validar"):
    dni_v = query.get("validar")
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    if df is not None:
        doc = df[df['DNI'] == dni_v]
        if not doc.empty:
            st.markdown(f"""
                <div style="text-align: center; border: 1px solid #eaeaea; padding: 50px; border-radius: 4px;">
                    <p style="text-transform: uppercase; letter-spacing: 3px; color: #999; font-size: 10px; margin-bottom: 20px;">Verificación de Autenticidad</p>
                    <h2 style="color: #2c5e2e; font-weight: 300;">✓ Documento Válido</h2>
                    <h1 style="font-weight: 600; font-size: 28px; color: #000;">{doc.iloc[0]['Nombre']}</h1>
                    <p style="color: #666;">DNI {dni_v}</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Registro no localizado.")
    st.stop()

# --- PANTALLA PRINCIPAL ---
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; font-weight: 300; color: #000;'>Portal de Certificación</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888; font-size: 14px;'>Ingrese su documento para emitir el certificado oficial.</p>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    dni_input = st.text_input("DNI", label_visibility="collapsed", placeholder="Número de DNI")
    
    if dni_input and df is not None:
        res = df[df['DNI'] == dni_input]
        if not res.empty:
            nombre_doc = res.iloc[0]['Nombre']
            with st.spinner("Generando..."):
                pdf_file = generar_pdf(nombre_doc, dni_input)
                if pdf_file:
                    st.download_button(
                        label="DESCARGAR PDF",
                        data=pdf_file,
                        file_name=f"Certificado_{dni_input}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
        else:
            st.markdown("<p style='text-align: center; color: #900; font-size: 12px;'>DNI no registrado.</p>", unsafe_allow_html=True)
