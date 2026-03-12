import streamlit as st
import pandas as pd
from PIL import Image
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape
from reportlab.lib.utils import ImageReader
import io
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema de Certificación Oficial", page_icon="🎓", layout="wide")

# --- ESTILOS ---
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 5px; padding: 10px; }
    .stTabs [aria-selected="true"] { background-color: #007bff; color: white; }
    </style>
""", unsafe_allow_html=True)

# --- CARGA DE DATOS ---
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

# --- FUNCIÓN GENERAR PDF CON QR ---
def generar_pdf_certificado(nombre, dni):
    # 1. Crear el QR de validación (URL de tu app + DNI)
    # Reemplaza la URL de abajo por la URL real de tu app en Streamlit Cloud
    url_validacion = f"https://certificados-9fnndcn82jqmyappo29hipd.streamlit.app/?dni_verificar={dni}"
    qr = qrcode.make(url_validacion)
    qr_img = io.BytesIO()
    qr.save(qr_img, format='PNG')
    qr_img.seek(0)

    # 2. Configurar el lienzo PDF (Basado en tamaño de imagen original)
    buffer = io.BytesIO()
    plantilla = Image.open("plantilla.png")
    ancho, alto = plantilla.size
    
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))
    
    # 3. Dibujar Plantilla de Fondo
    c.drawImage("plantilla.png", 0, 0, width=ancho, height=alto)
    
    # 4. Configurar Fuentes y Escribir (Ajusta coordenadas según tu plantilla)
    # Intentamos cargar Arial, si no usamos Helvetica (estándar en PDF)
    try:
        c.setFont("Helvetica-Bold", 120) 
    except:
        c.setFont("Helvetica", 100)

    # Nombre (Centrado en X=2351, Y=1575)
    c.drawCentredString(2351, 4575, nombre.upper())
    
    # DNI
     # c.setFont("Helvetica", 100)
    c.drawCentredString(4803, 4575, f"DNI: {dni}")

    # 5. Dibujar Código QR en una esquina (ejemplo: abajo a la derecha)
    c.drawImage(ImageReader(qr_img), ancho - 500, 100, width=350, height=350)
    
    # Texto de ayuda bajo el QR
    c.setFont("Helvetica", 40)
    c.drawString(ancho - 500, 50, "Escanee para validar autenticidad")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- INTERFAZ DE USUARIO ---
st.title("🎓 Jornada dia 26 de Marzo")

tab1, tab2 = st.tabs(["📥 Descargar mi Certificado", "🔍 Verificar Autenticidad"])

with tab1:
    st.header("Obtén tu comprobante oficial")
    dni_input = st.text_input("Ingresa tu DNI para buscar:", key="descarga")
    
    if dni_input and df is not None:
        resultado = df[df['DNI'] == dni_input]
        if not resultado.empty:
            nombre = resultado.iloc[0]['Nombre']
            st.success(f"Certificado localizado: **{nombre}**")
            
            with st.spinner("Generando PDF oficial..."):
                pdf_file = generar_pdf_certificado(nombre, dni_input)
                
            st.download_button(
                label="⬇️ Descargar Certificado en PDF",
                data=pdf_file,
                file_name=f"Certificado_{dni_input}.pdf",
                mime="application/pdf"
            )
        else:
            st.error("El DNI no figura en nuestra base de datos de aprobados.")

with tab2:
    st.header("Validador de Títulos")
    st.write("Cualquier institución puede verificar la validez de un certificado aquí.")
    
    # Soporte para validación automática vía QR
    query_params = st.query_params
    dni_auto = query_params.get("dni_verificar", "")
    
    dni_verificar = st.text_input("Ingrese el DNI a verificar:", value=dni_auto, key="verif")
    
    if dni_verificar and df is not None:
        verif_res = df[df['DNI'] == dni_verificar]
        if not verif_res.empty:
            st.balloons()
            st.success(f"✅ **CERTIFICADO AUTÉNTICO**")
            st.write(f"**Alumno:** {verif_res.iloc[0]['Nombre']}")
            st.write(f"**Estado:** Aprobado / Asistencia Confirmada")
            st.write(f"**Institución:** [Tu Nombre de Institución]")
        else:
            st.error("❌ El certificado no es válido o el DNI no existe en los registros oficiales.")

st.divider()
st.caption("Sistema Seguro de Certificación - 2026")


