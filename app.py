import streamlit as st
import pandas as pd
from PIL import Image
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Certificados Oficiales", page_icon="🎓", layout="centered")

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    try:
        # Cargamos el Excel
        df = pd.read_excel("asistentes.xlsx", dtype={'DNI': str})
        df['DNI'] = df['DNI'].str.strip()
        df['Nombre'] = df['Nombre'].str.strip()
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo Excel: {e}")
        return None

df = cargar_datos()

# --- FUNCIÓN PARA GENERAR EL PDF ---
def generar_pdf(nombre, dni):
    # 1. Crear el QR
    # CAMBIA ESTE LINK por el tuyo real de Streamlit
    link_web = "https://certificados-9fnndcn82jqmyappo29hipd.streamlit.app/"
    url_validacion = f"{link_web}?dni_verificar={dni}"
    
    qr = qrcode.make(url_validacion)
    qr_img = io.BytesIO()
    qr.save(qr_img, format='PNG')
    qr_img.seek(0)

    # 2. Preparar el PDF
    buffer = io.BytesIO()
    plantilla = Image.open("plantilla.png")
    ancho, alto = plantilla.size
    
    # Creamos el canvas con el tamaño de tu imagen
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))
    
    # Dibujar fondo
    c.drawImage("plantilla.png", 0, 0, width=ancho, height=alto)
    
    # Dibujar Nombre (Ajusta coordenadas 2351, 1575 si es necesario)
    c.setFont("Helvetica-Bold", 110)
    c.drawCentredString(2351, 1575, nombre.upper())
    
    # Dibujar DNI
    c.setFont("Helvetica", 70)
    c.drawCentredString(4803, 1575, f"DNI: {dni}")

    # Dibujar QR (Esquina inferior derecha)
    c.drawImage(ImageReader(qr_img), ancho - 600, 150, width=400, height=400)
    
    # Texto de validación
    c.setFont("Helvetica", 35)
    c.drawString(ancho - 600, 100, "Validar en: " + link_web)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- INTERFAZ ---
st.title("🎓 Descarga tu Certificado Docente")
st.write("Ingresa tu DNI para generar el documento oficial en PDF.")

# Lógica de validación por URL (para el QR)
query_params = st.query_params
dni_verif = query_params.get("dni_verificar", None)

if dni_verif:
    st.info(f"🔍 Verificando autenticidad del DNI: {dni_verif}")
    if df is not None:
        v = df[df['DNI'] == dni_verif]
        if not v.empty:
            st.success(f"✅ CERTIFICADO VÁLIDO: {v.iloc[0]['Nombre']}")
            st.balloons()
        else:
            st.error("❌ Certificado no encontrado en registros oficiales.")
    st.divider()

# Sección de descarga
dni_input = st.text_input("Escribe tu DNI aquí:")

if dni_input and df is not None:
    resultado = df[df['DNI'] == dni_input]
    
    if not resultado.empty:
        nombre_docente = resultado.iloc[0]['Nombre']
        st.success(f"¡Hola {nombre_docente}! Hemos generado tu certificado.")
        
        # Generamos el PDF
        pdf_data = generar_pdf(nombre_docente, dni_input)
        pdf_bytes = pdf_data.getvalue()
        
        # --- MOSTRAR PDF EN PANTALLA ---
        # Convertimos a base64 para que el navegador lo pueda leer
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
        
        st.write(" ") # Espacio
        
        # Botón de descarga
        st.download_button(
            label="⬇️ Descargar Certificado (PDF)",
            data=pdf_bytes,
            file_name=f"Certificado_{dni_input}.pdf",
            mime="application/pdf"
        )
    else:
        st.error("El DNI no se encuentra en la lista de aprobados.")
