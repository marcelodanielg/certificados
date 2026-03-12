import streamlit as st
import pandas as pd
import qrcode
import io
import os
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# 1. CONFIGURACIÓN DE UBICACIÓN
X_TEXTO = 300
Y_TEXTO = 240
TAMANO_LETRA = 20

X_QR = 690
Y_QR = 425
TAMANO_QR = 100

st.set_page_config(page_title="Certificados", layout="centered")

# Limpieza visual
st.markdown("<style>#MainMenu, footer, header {visibility: hidden;}</style>", unsafe_allow_html=True)

@st.cache_data
def cargar_datos():
    if not os.path.exists("asistentes.xlsx"):
        st.error("⚠️ Archivo 'asistentes.xlsx' no encontrado en GitHub.")
        return None
    try:
        return pd.read_excel("asistentes.xlsx", dtype={'DNI': str})
    except Exception as e:
        st.error(f"⚠️ Error al leer el Excel: {e}")
        return None

df = cargar_datos()

def generar_pdf(nombre, dni):
    if not os.path.exists("plantilla.png"):
        st.error("⚠️ Archivo 'plantilla.png' no encontrado en GitHub.")
        return None
        
    buffer = io.BytesIO()
    plantilla = Image.open("plantilla.png")
    ancho, alto = plantilla.size
    
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))
    c.drawImage("plantilla.png", 0, 0, width=ancho, height=alto)
    
    # Escribir Nombre y DNI
    c.setFont("Helvetica-Bold", TAMANO_LETRA)
    c.drawCentredString(X_TEXTO, alto - Y_TEXTO, f"{nombre.upper()} - DNI: {dni}")
    
    # Generar y pegar QR
    # Reemplaza 'tu-app' por el nombre real de tu url si lo deseas
    qr = qrcode.make(f"https://certificados.streamlit.app/?v={dni}")
    qr_buf = io.BytesIO()
    qr.save(qr_buf, format='PNG')
    qr_buf.seek(0)
    c.drawImage(ImageReader(qr_buf), X_QR, alto - (Y_QR + TAMANO_QR), width=TAMANO_QR, height=TAMANO_QR)
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- INTERFAZ ---
st.title("🎓 Portal de Certificados")

# Validación QR
query = st.query_params
if query.get("v"):
    dni_v = query.get("v")
    if df is not None:
        doc = df[df['DNI'] == dni_v]
        if not doc.empty:
            st.success(f"✅ DOCUMENTO VÁLIDO: {doc.iloc[0]['Nombre']}")
    st.stop()

dni_input = st.text_input("Ingresa tu DNI:", placeholder="Sin puntos ni espacios")

if dni_input and df is not None:
    # Limpiamos el input por si acaso
    dni_limpio = dni_input.strip()
    res = df[df['DNI'] == dni_limpio]
    
    if not res.empty:
        nombre_doc = res.iloc[0]['Nombre']
        st.info(f"Certificado para: **{nombre_doc}**")
        
        pdf = generar_pdf(nombre_doc, dni_limpio)
        if pdf:
            st.download_button(
                label="⬇️ DESCARGAR CERTIFICADO",
                data=pdf,
                file_name=f"Certificado_{dni_limpio}.pdf",
                mime="application/pdf"
            )
    else:
        st.error("DNI no registrado en la base de datos.")
