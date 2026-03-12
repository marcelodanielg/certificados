import streamlit as st
import pandas as pd
import qrcode
import io
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# 1. CONFIGURACIÓN DE UBICACIÓN (Cambia estos números a tu gusto)
# ----------------------------------------------------------------
X_TEXTO = 300     # Centro de la hoja (Horizontal)
Y_TEXTO =  240     # Altura desde arriba (Vertical)
TAMANO_LETRA = 20

X_QR = 690        # Posición derecha
Y_QR = 425        # Posición abajo
TAMANO_QR = 100
# ----------------------------------------------------------------

st.set_page_config(page_title="Certificados", layout="centered")

# Limpieza visual (Sin menús ni marcas de agua)
st.markdown("<style>#MainMenu, footer, header {visibility: hidden;}</style>", unsafe_allow_html=True)

@st.cache_data
def cargar_datos():
    try:
        return pd.read_excel("asistentes.xlsx", dtype={'DNI': str})
    except:
        st.error("Sube 'asistentes.xlsx' a GitHub")
        return None

df = cargar_datos()

def generar_pdf(nombre, dni):
    buffer = io.BytesIO()
    plantilla = Image.open("plantilla.png")
    ancho, alto = plantilla.size
    
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))
    c.drawImage("plantilla.png", 0, 0, width=ancho, height=alto)
    
    # Escribir Nombre y DNI
    c.setFont("Helvetica-Bold", TAMANO_LETRA)
    c.drawCentredString(X_TEXTO, alto - Y_TEXTO, f"{nombre.upper()} - DNI: {dni}")
    
    # Generar y pegar QR
    qr = qrcode.make(f"https://tu-app.streamlit.app/?v={dni}")
    qr_buf = io.BytesIO()
    qr.save(qr_buf, format='PNG')
    c.drawImage(ImageReader(qr_buf), X_QR, alto - (Y_QR + TAMANO_QR), width=TAMANO_QR, height=TAMANO_QR)
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- PANTALLA ---
st.title("🎓 Portal de Certificados")

# Validación rápida si escanean el QR
if st.query_params.get("v"):
    dni_v = st.query_params.get("v")
    if df is not None:
        doc = df[df['DNI'] == dni_v]
        if not doc.empty:
            st.success(f"✅ VÁLIDO: {doc.iloc[0]['Nombre']}")
    st.stop()

dni_input = st.text_input("Ingresa tu DNI:")

if dni_input and df is not None:
    res = df[df['DNI'] == dni_input]
    if not res.empty:
        nombre_doc = res.iloc[0]['Nombre']
        st.write(f"Certificado para: **{nombre_doc}**")
        pdf = generar_pdf(nombre_doc, dni_input)
        st.download_button("⬇️ DESCARGAR PDF", data=pdf, file_name=f"Certificado_{dni_input}.pdf")
    else:
        st.error("DNI no registrado.")







