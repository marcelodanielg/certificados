import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Portal de Certificados", page_icon="🎓")

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("asistentes.xlsx", dtype={'DNI': str})
        df['DNI'] = df['DNI'].str.strip()
        df['Nombre'] = df['Nombre'].str.strip()
        return df
    except Exception as e:
        st.error(f"Error al cargar Excel")
        return None

# =========================================================
# ⚙️ CONFIGURACIÓN DEL ADMINISTRADOR (Solo tú editas esto)
# =========================================================
# 1. Ejecuta la app con los sliders una vez, busca los números y luego ponlos aquí:
LINK_APP = "https://certificados-9fnndcn82jqmyappo29hipd.streamlit.app/"

# Coordenadas para Nombre y DNI (Mismo renglón)
TXT_X = 60   # Centro horizontal
TXT_Y = 216    # Altura desde arriba (Primera cuarta parte)
TXT_SIZE = 95  # Tamaño de letra

# Coordenadas para el Código QR
QR_X = 800    # Posición horizontal del QR
QR_Y = 600    # Posición vertical del QR (Cerca del borde inferior)
QR_SIZE = 150  # Tamaño del cuadrado del QR
# =========================================================

df = cargar_datos()

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
    
    # Dibujar Texto (ReportLab mide desde abajo, por eso restamos)
    c.setFont("Helvetica-Bold", TXT_SIZE)
    c.drawCentredString(TXT_X, alto - TXT_Y, f"{nombre.upper()} - DNI: {dni}")
    
    # Dibujar QR
    c.drawImage(ImageReader(qr_buf), QR_X, alto - QR_Y, width=QR_SIZE, height=QR_SIZE)
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- LÓGICA DE LA APP ---

# MODO VALIDADOR (Para el QR)
if st.query_params.get("validar"):
    dni_v = st.query_params.get("validar")
    st.title("🔍 Validación de Autenticidad")
    if df is not None:
        doc = df[df['DNI'] == dni_v]
        if not doc.empty:
            st.success(f"### ✅ CERTIFICADO VÁLIDO\n**Titular:** {doc.iloc[0]['Nombre']}")
            st.balloons()
        else:
            st.error("### ❌ CERTIFICADO NO ENCONTRADO")
    st.stop()

# MODO USUARIO (Lo que ven los alumnos)
st.title("🎓 Descarga de Certificados")
st.write("Ingrese su DNI para obtener el documento oficial.")

dni_input = st.text_input("DNI:")

if dni_input and df is not None:
    res = df[df['DNI'] == dni_input]
    if not res.empty:
        nombre_doc = res.iloc[0]['Nombre']
        st.info(f"Certificado listo para: {nombre_doc}")
        
        pdf_file = generar_pdf(nombre_doc, dni_input)
        
        st.download_button(
            label="⬇️ Descargar Certificado (PDF)",
            data=pdf_file,
            file_name=f"Certificado_{dni_input}.pdf",
            mime="application/pdf"
        )
    else:
        st.error("DNI no encontrado.")

