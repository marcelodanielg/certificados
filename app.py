import io
import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
import streamlit as st

# --- 1. CONFIGURACIÓN DE PÁGINA ---
X_TEXTO, Y_TEXTO, TAM_LETRA = 300, 265, 20

st.set_page_config(
    page_title="Constancias de Asistencia", 
    page_icon="📜",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. DISEÑO COMPACTO Y VERSÁTIL (IDEAL CELULAR Y PC) ---
st.markdown(
    """
    <style>
    #MainMenu, footer, header { display: none !important; }
    .block-container {
        padding-top: 0.8rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 600px !important;
    }
    .stApp { background-color: #f8fafc; }

    /* Encabezado ultra compacto */
    .compact-header {
        text-align: center;
        padding: 10px;
        background: linear-gradient(135deg, #1b4965 0%, #2b5876 100%);
        color: white;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .compact-header h1 { margin: 0; font-size: 18px; font-weight: 700; }
    .compact-header p { margin: 2px 0 0 0; font-size: 11px; opacity: 0.9; }

    /* Formulario minimalista */
    div[data-testid="stForm"] {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #cbd5e1;
        margin-bottom: 10px;
    }
    div[data-testid="stForm"] label { font-size: 12px !important; font-weight: bold !important; color: #1b4965 !important; }

    /* Tarjetas de eventos encontrados compactas */
    .tarjeta-resultado {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #1b4965;
        border-radius: 6px;
        padding: 8px 12px;
        margin-bottom: 8px;
        font-size: 12px;
        color: #1e293b;
    }

    /* Botones de descarga rápidos */
    .stDownloadButton>button {
        background-color: #1b4965 !important;
        color: #ffffff !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        padding: 6px 10px !important;
        border-radius: 6px !important;
        border: none !important;
        width: 100% !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- 3. CARGA GLOBAL DE EVENTOS ---
@st.cache_data(ttl=3600)
def cargar_todos_los_eventos():
    directorio_eventos = "eventos"
    registros_totales = []

    if not os.path.exists(directorio_eventos):
        return registros_totales

    for nombre_carpeta in os.listdir(directorio_eventos):
        ruta_carpeta = os.path.join(directorio_eventos, nombre_carpeta)
        
        if os.path.isdir(ruta_carpeta):
            path_xlsx = os.path.join(ruta_carpeta, "asistentes.xlsx")
            path_plantilla = os.path.join(ruta_carpeta, "plantilla.png")

            if os.path.exists(path_xlsx) and os.path.exists(path_plantilla):
                try:
                    df = pd.read_excel(path_xlsx)
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

                        registros_totales.append({
                            "evento": nombre_carpeta,
                            "df": df,
                            "path_plantilla": path_plantilla
                        })
                except Exception as e:
                    print(f"Error procesando {nombre_carpeta}: {e}")

    return registros_totales

eventos_disponibles = cargar_todos_los_eventos()


def generar_pdf(nombre, dni, path_plantilla):
    buffer = io.BytesIO()
    img_temp = Image.open(path_plantilla)
    ancho, alto = img_temp.size

    c = canvas.Canvas(buffer, pagesize=(ancho, alto))
    c.drawImage(path_plantilla, 0, 0, width=ancho, height=alto)
    c.setFont("Helvetica-Bold", TAM_LETRA)
    c.drawCentredString(X_TEXTO, alto - Y_TEXTO, f"{nombre.upper()} - DNI: {dni}")
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


# --- 4. INTERFAZ DE USUARIO COMPACTA ---
st.markdown(
    """
    <div class='compact-header'>
        <h1>📜 Constancias de Asistencia</h1>
        <p>Ingrese su DNI para obtener sus certificados</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Inicializar estados de memoria para evitar que se borren los resultados
if "resultados" not in st.session_state:
    st.session_state.resultados = None
if "dni_buscado" not in st.session_state:
    st.session_state.dni_buscado = ""

if eventos_disponibles:
    # Formulario compacto de una sola línea horizontal
    with st.form(key="form_dni_compacto"):
        col_input, col_btn = st.columns([3, 1])
        with col_input:
            dni_input = st.text_input("DNI (sin puntos):", placeholder="Ej: 25123456", label_visibility="collapsed")
        with col_btn:
            submit_button = st.form_submit_button(label="🔍 Buscar", use_container_width=True)

    if submit_button and dni_input:
        dni_limpio = "".join(filter(str.isdigit, dni_input))
        st.session_state.dni_buscado = dni_limpio
        encontrados = []

        for ev in eventos_disponibles:
            df_temp = ev["df"]
            res = df_temp[df_temp["DNI"] == dni_limpio]
            if not res.empty:
                encontrados.append({
                    "evento": ev["evento"],
                    "nombre": res.iloc[0]["Nombre"],
                    "path_plantilla": ev["path_plantilla"]
                })
        st.session_state.resultados = encontrados

    # Mostrar resultados almacenados (Garantiza que funcione perfecto en celulares)
    if st.session_state.resultados is not None:
        encontrados = st.session_state.resultados
        
        if encontrados:
            st.success(f"Se encontraron **{len(encontrados)}** constancia(s) para el DNI {st.session_state.dni_buscado}:")
            
            for item in encontrados:
                fecha_evento = item["evento"]
                nombre_doc = item["nombre"]
                path_plantilla = item["path_plantilla"]

                # Generar PDF en memoria de forma ultrarrápida
                pdf_data = generar_pdf(nombre_doc, st.session_state.dni_buscado, path_plantilla)

                # Diseño en filas compactas (Información a la izquierda, Botón a la derecha)
                c_info, c_down = st.columns([2, 1])
                with c_info:
                    st.markdown(
                        f"""
                        <div class='tarjeta-resultado'>
                            <b>📅 Evento:</b> {fecha_evento}<br>
                            <b>👤 Docente:</b> {nombre_doc}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with c_down:
                    st.download_button(
                        label="📥 Descargar",
                        data=pdf_data,
                        file_name=f"Constancia_{st.session_state.dni_buscado}_{fecha_evento}.pdf",
                        mime="application/pdf",
                        key=f"dl_{fecha_evento}"
                    )
        else:
            st.error("El DNI ingresado no figura en las nóminas.")
else:
    st.warning("⚠️ No hay carpetas de eventos configuradas en el repositorio.")
