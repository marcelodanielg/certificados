import io
import os
import pandas as pd
from PIL import Image
from reportlab.pdfgen import canvas
import streamlit as st

# --- 1. CONFIGURACIÓN E INTERFAZ ---
X_TEXTO, Y_TEXTO, TAM_LETRA = 300, 265, 20

st.set_page_config(
    page_title="Constancia de Asistencia", 
    page_icon="📜",
    layout="centered"
)

# Estilos CSS
st.markdown(
    """
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    #stDecoration {display:none;}
    .stApp { background-color: #f4f6f9; }
    
    .header-container {
        text-align: center;
        padding: 20px 10px;
        margin-bottom: 20px;
        background: linear-gradient(135deg, #1b4965 0%, #2b5876 100%);
        border-radius: 12px;
        color: white;
    }
    .header-container h1 { margin: 0; font-size: 26px; font-weight: 700; }
    .header-container p { margin-top: 8px; font-size: 14px; opacity: 0.9; }

    .tarjeta-bienvenida {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #e0e0e0;
        margin-bottom: 25px;
    }

    div[data-testid="stForm"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #1b4965;
        margin-bottom: 20px;
    }
    div[data-testid="stForm"] label { font-size: 18px !important; font-weight: bold !important; color: #1b4965 !important; }
    div[data-testid="stForm"] input { font-size: 18px !important; padding: 10px !important; }

    .tarjeta-info {
        background-color: #ffffff;
        border-left: 5px solid #1b4965;
        padding: 18px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- 2. OPTIMIZACIÓN DE MEMORIA (CACHÉ COMPARTIDA) ---

@st.cache_resource
def obtener_dimensiones_plantilla():
    """Obtiene el tamaño de la plantilla una sola vez para no abrir la imagen constantemente"""
    if os.path.exists("plantilla.png"):
        with Image.open("plantilla.png") as img:
            return img.size
    return (800, 600)

@st.cache_data(ttl=3600)
def cargar_base_docentes():
    """
    Procesa el Excel 1 sola vez para todo el servidor.
    Indexa en un diccionario DNI -> Nombre para búsquedas instantáneas en RAM.
    """
    if os.path.exists("asistentes.xlsx"):
        df = pd.read_excel("asistentes.xlsx")
        df.columns = df.columns.str.strip()

        if "Nombre" in df.columns and "DNI" in df.columns:
            muestra_dni = df["DNI"].dropna().astype(str)
            if muestra_dni.str.contains(r"[a-zA-ZñÑ]").any():
                df = df.rename(columns={"Nombre": "DNI_temporal", "DNI": "Nombre"})
                df = df.rename(columns={"DNI_temporal": "DNI"})

            df = df.dropna(subset=["DNI"])
            df["DNI"] = (
                df["DNI"]
                .astype(str)
                .str.replace(r"\.0$", "", regex=True)
                .str.replace(r"\D", "", regex=True)
            )
            df["Nombre"] = df["Nombre"].astype(str).str.strip()

            # Diccionario en RAM: {"25123456": "JUAN PEREZ"}
            return dict(zip(df["DNI"], df["Nombre"]))
    return {}


# Carga global única
asistentes_dict = cargar_base_docentes()
ancho_p, alto_p = obtener_dimensiones_plantilla()


# --- 3. GENERACIÓN LIGERA DE PDF EN STREAMING ---

def construir_pdf(nombre, dni):
    """Genera el PDF directamente usando ReportLab en memoria RAM sin llamadas a disco"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(ancho_p, alto_p))
    
    # Dibuja la plantilla guardada en disco y superpone el texto
    c.drawImage("plantilla.png", 0, 0, width=ancho_p, height=alto_p)
    c.setFont("Helvetica-Bold", TAM_LETRA)
    c.drawCentredString(X_TEXTO, alto_p - Y_TEXTO, f"{nombre.upper()} - DNI: {dni}")
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


# --- 4. FLUJO DE LA APLICACIÓN ---

st.markdown(
    """
    <div class='header-container'>
        <h1>📜 Constancia de Asistencia</h1>
        <p>Sistema Digital de Emisión de Comprobantes</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if asistentes_dict:
    st.markdown(
        """
        <div class='tarjeta-bienvenida'>
            <h4>Bienvenido/a</h4>
            <p style='margin:0; font-size:14px; color:#555;'>Ingrese su número de DNI para obtener su constancia.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form(key="form_dni"):
        dni_input = st.text_input("Ingrese su número de DNI:", placeholder="Ej: 25123456")
        submit_button = st.form_submit_button(label="Buscar", use_container_width=True)

    if submit_button and dni_input:
        dni_limpio = "".join(filter(str.isdigit, dni_input))
        
        # Búsqueda ultra rápida en memoria RAM (O(1))
        nombre_doc = asistentes_dict.get(dni_limpio)

        if nombre_doc:
            pdf_bytes = construir_pdf(nombre_doc, dni_limpio)

            st.markdown(
                f"""
                <div class='tarjeta-info'>
                    <b>Docente:</b> {nombre_doc}<br>
                    Su comprobante está listo:
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.download_button(
                label="📥 DESCARGAR DOCUMENTO (PDF)",
                data=pdf_bytes,
                file_name=f"Constancia_{dni_limpio}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.error("El DNI ingresado no se encuentra registrado en la nómina de asistentes.")
else:
    st.warning("No se encontró el archivo 'asistentes.xlsx' en el servidor.")
