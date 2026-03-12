import streamlit as st
import pandas as pd
import qrcode
import io
import os
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# --- 1. CONFIGURACIÓN DE DISEÑO (Ajusta aquí) ---
X_TEXTO = 300
Y_TEXTO = 240
TAMANO_LETRA = 20

X_QR = 690
Y_QR = 425
TAMANO_QR = 100

# REEMPLAZA ESTO POR EL LINK DE TU APP EN STREAMLIT CLOUD
URL_BASE = "https://certificados-9fnndcn82jqmyappo29hipd.streamlit.app/" 
# ------------------------------------------------

st.set_page_config(page_title="Sistema de Certificados", layout="centered")

# CSS para eliminar TODA la publicidad y marcas de la plataforma
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    #stDecoration {display:none;}
    [data-testid="stStatusWidget"] {visibility: hidden;}
    .stDeployButton {display:none;}
    .stApp { background-color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def cargar_datos():
    if not os.path.exists("asistentes.xlsx"):
        return None
    try:
        return pd.read_excel("asistentes.xlsx", dtype={'DNI': str})
    except:
        return None

df = cargar_datos()

def generar_pdf(nombre, dni):
    if not os.path.exists("plantilla.png"):
        st.error("Archivo plantilla.png no encontrado.")
        return None
        
    buffer = io.BytesIO()
    plantilla = Image.open("plantilla.png")
    ancho, alto = plantilla.size
    
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))
    c.drawImage("plantilla.png", 0, 0, width=ancho, height=alto)
    
    # Escribir Nombre y DNI
    c.setFont("Helvetica-Bold", TAMANO_LETRA)
    c.drawCentredString(X_TEXTO, alto - Y_TEXTO, f"{nombre.upper()} - DNI: {dni}")
    
    # GENERAR QR DE VALIDACIÓN
    # El QR enviará al usuario a la app con el parámetro ?v=DNI
    enlace_validacion = f"{URL_BASE}?v={dni}"
    qr = qrcode.make(enlace_validacion)
    qr_buf = io.BytesIO()
    qr.save(qr_buf, format='PNG')
    qr_buf.seek(0)
    
    c.drawImage(ImageReader(qr_buf), X_QR, alto - (Y_QR + TAMANO_QR), width=TAMANO_QR, height=TAMANO_QR)
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- LÓGICA DE PANTALLAS ---

# Detectar si alguien escaneó el QR (Parámetro 'v' en la URL)
query = st.query_params
if "v" in query:
    dni_v = query["v"]
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    if df is not None:
        doc = df[df['DNI'] == dni_v]
        if not doc.empty:
            st.markdown(f"""
                <div style="text-align: center; border: 2px solid #2e7d32; padding: 40px; border-radius: 10px;">
                    <h2 style="color: #2e7d32;">✅ CERTIFICADO AUTÉNTICO</h2>
                    <h1 style="color: #1a1a1a;">{doc.iloc[0]['Nombre']}</h1>
                    <p style="color: #666;">Documento validado por el sistema oficial.</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error("El código escaneado no pertenece a un certificado válido.")
    st.stop()

# Pantalla normal para el docente
st.markdown("<h2 style='text-align: center;'>Portal de Certificados</h2>", unsafe_allow_html=True)
st.write("---")

if df is None:
    st.error("Error al cargar la base de datos. Verifica el archivo asistentes.xlsx")
else:
    dni_input = st.text_input("Ingrese su DNI:", placeholder="Ej: 12345678")
    
    if dni_input:
        dni_limpio = dni_input.strip()
        res = df[df['DNI'] == dni_limpio]
        
        if not res.empty:
            nombre_doc = res.iloc[0]['Nombre']
            st.info(f"Certificado para: {nombre_doc}")
            
            pdf = generar_pdf(nombre_doc, dni_limpio)
            if pdf:
                st.download_button(
                    label="DESCARGAR CERTIFICADO (PDF)",
                    data=pdf,
                    file_name=f"Certificado_{dni_limpio}.pdf",
                    mime="application/pdf"
                )
        else:
            st.error("DNI no registrado.")
