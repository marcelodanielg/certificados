import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Validador de Certificados", page_icon="🎓")

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("asistentes.xlsx", dtype={'DNI': str})
        df['DNI'] = df['DNI'].str.strip()
        df['Nombre'] = df['Nombre'].str.strip()
        return df
    except Exception as e:
        st.error(f"Error al cargar Excel: {e}")
        return None

df = cargar_datos()

# --- CONSTANTES DE DISEÑO ---
# Ajusta este link por el tuyo real de Streamlit
LINK_APP = "https://certificados-9fnndcn82jqmyappo29hipd.streamlit.app/"
TAMANO_FUENTE = 90

# --- FUNCIÓN GENERAR PDF ---
def generar_pdf(nombre, dni):
    # El QR ahora lleva un parámetro especial '?validar='
    url_validacion = f"{LINK_APP}?validar={dni}"
    
    qr = qrcode.make(url_validacion)
    qr_img = io.BytesIO()
    qr.save(qr_img, format='PNG')
    qr_img.seek(0)

    buffer = io.BytesIO()
    plantilla = Image.open("plantilla.png")
    ancho, alto = plantilla.size
    
    # Posición Y (cuarta parte superior en PDF)
    pos_y_pdf = alto * 0.75 

    c = canvas.Canvas(buffer, pagesize=(ancho, alto))
    c.drawImage("plantilla.png", 0, 0, width=ancho, height=alto)
    
    # Texto en el mismo renglón
    texto_completo = f"{nombre.upper()} - DNI: {dni}"
    c.setFont("Helvetica-Bold", TAMANO_FUENTE)
    c.drawCentredString(ancho / 2, pos_y_pdf, texto_completo)
    
    # QR de Validación
    c.drawImage(ImageReader(qr_img), ancho - 550, 150, width=350, height=350)
    c.setFont("Helvetica", 40)
    c.drawString(ancho - 550, 100, "Escanee para validar")
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- LÓGICA DE LA APLICACIÓN ---

# 1. VERIFICAR SI VIENE DESDE EL QR
query_params = st.query_params
dni_a_validar = query_params.get("validar")

if dni_a_validar:
    # Si existe este parámetro, mostramos SOLO la validación
    st.title("🔍 Validación de Certificado")
    if df is not None:
        docente = df[df['DNI'] == dni_a_validar]
        if not docente.empty:
            st.success("### ✅ CERTIFICADO AUTÉNTICO")
            st.balloons()
            st.write(f"**Nombre del titular:** {docente.iloc[0]['Nombre']}")
            st.write(f"**Documento:** {dni_a_validar}")
            st.write("**Estado:** Registrado en la base de datos oficial.")
        else:
            st.error("### ❌ CERTIFICADO NO VÁLIDO")
            st.write("El documento escaneado no coincide con nuestros registros oficiales.")
    
    if st.button("Ir al sitio de descargas"):
        st.query_params.clear()
        st.rerun()
    st.stop() # Detiene la ejecución para que no se vea el formulario de abajo

# 2. INTERFAZ NORMAL DE DESCARGA
st.title("🎓 Descarga de Certificados")
st.write("Ingrese su DNI para obtener su certificado oficial.")

dni_input = st.text_input("DNI:")

if dni_input and df is not None:
    res = df[df['DNI'] == dni_input]
    if not res.empty:
        nombre = res.iloc[0]['Nombre']
        
        # Vista previa rápida (opcional, puedes quitarla si prefieres solo el botón)
        st.info(f"Certificado encontrado para: {nombre}")
        
        # Botón de descarga
        pdf_file = generar_pdf(nombre, dni_input)
        st.download_button(
            label="⬇️ Descargar PDF con QR de Validación",
            data=pdf_file,
            file_name=f"Certificado_{dni_input}.pdf",
            mime="application/pdf"
        )
    else:
        st.error("El DNI no se encuentra en la lista.")
