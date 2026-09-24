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

# --- 2. DISEÑO ULTRALIVIANO PARA MÁXIMA VELOCIDAD EN MÓVIL ---
st.markdown(
    """
    <style>
    #MainMenu, footer, header, .stDeployButton, #stDecoration { display: none !important; }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 700px !important;
    }
    .stApp { background-color: #f8fafc; }

    .header-container {
        text-align: center;
        padding: 15px;
        margin-bottom: 12px;
        background: linear-gradient(135deg, #1b4965 0%, #2b5876 100%);
        border-radius: 10px;
        color: white;
    }
    .header-container h1 { margin: 0; font-size: 22px; font-weight: 700; }
    .header-container p { margin: 4px 0 0 0; font-size: 12px; opacity: 0.9; }

    .tarjeta-bienvenida {
        background-color: #ffffff; border-radius: 8px; padding: 12px 15px;
        border: 1px solid #e2e8f0; margin-bottom: 12px; font-size: 13px; color: #334155;
    }
    .pasos-lista { margin: 4px 0 0 0; padding-left: 18px; font-size: 12px; line-height: 1.3; }

    div[data-testid="stForm"] {
        background-color: #ffffff; padding: 15px; border-radius: 10px;
        border: 2px solid #1b4965; margin-bottom: 12px;
    }
    div[data-testid="stForm"] label { font-size: 14px !important; font-weight: bold !important; color: #1b4965 !important; }
    div[data-testid="stForm"] input { font-size: 16px !important; padding: 8px !important; }

    .tarjeta-evento {
        background-color: #ffffff; border: 1px solid #cbd5e1; border-left: 4px solid #1b4965;
        border-radius: 8px; padding: 12px; margin-bottom: 10px; font-size: 13px; color: #1e293b;
    }

    .stButton>button, .stDownloadButton>button {
        background-color: #1b4965 !important; color: #ffffff !important;
        font-size: 15px !important; font-weight: 700 !important; padding: 10px !important;
        border-radius: 6px !important; border: none !important; width: 100% !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- 3. CARGA GLOBAL Y CENTRALIZADA ---
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


# --- 4. INTERFAZ DE USUARIO ---
st.markdown(
    """
    <div class='header-container'>
        <h1>📜 Constancias de Asistencia</h1>
        <p>Sistema de Descarga Rápida</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if eventos_disponibles:
    st.markdown(
        """
        <div class='tarjeta-bienvenida'>
            <b>Instrucciones:</b>
            <ol class='pasos-lista'>
                <li>Ingrese su número de <b>DNI</b> sin puntos ni espacios.</li>
                <li>Seleccione las constancias que desea descargar o marque todas juntas.</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form(key="form_dni_global"):
        dni_input = st.text_input("Ingrese su DNI:", placeholder="Ej: 25123456")
        submit_button = st.form_submit_button(label="🔍 Buscar Mis Constancias", use_container_width=True)

    if submit_button and dni_input:
        dni_limpio = "".join(filter(str.isdigit, dni_input))
        encontrados = []

        for ev in eventos_disponibles:
            df_temp = ev["df"]
            res = df_temp[df_temp["DNI"] == dni_limpio]
            if not res.empty:
                nombre_doc = res.iloc[0]["Nombre"]
                encontrados.append({
                    "evento": ev["evento"],
                    "nombre": nombre_doc,
                    "path_plantilla": ev["path_plantilla"]
                })

        if encontrados:
            st.success(f"¡Se encontraron **{len(encontrados)}** constancia(s) para el DNI {dni_limpio}!")
            
            # Opción para tildar/seleccionar qué eventos descargar
            st.markdown("### Seleccione las constancias a descargar:")
            
            seleccionados = {}
            # Casilla para marcar/desmarcar todos de entrada
            marcar_todos = st.checkbox("☑️ Seleccionar / Deseleccionar Todos", value=True)

            st.markdown("---")

            for item in encontrados:
                fecha_evento = item["evento"]
                nombre_doc = item["nombre"]
                
                # Checkbox individual para cada evento
                seleccionados[fecha_evento] = st.checkbox(
                    f"📅 Evento: {fecha_evento} (Docente: {nombre_doc})", 
                    value=marcar_todos,
                    key=f"chk_{fecha_evento}"
                )

            st.markdown("---")

            # Botón único para procesar y descargar las seleccionadas
            if st.button("📥 DESCARGAR CONSTANCIAS SELECCIONADAS", use_container_width=True):
                alguna_seleccionada = False
                
                for item in encontrados:
                    fecha_evento = item["evento"]
                    if seleccionados.get(fecha_evento, False):
                        alguna_seleccionada = True
                        nombre_doc = item["nombre"]
                        path_plantilla = item["path_plantilla"]
                        
                        pdf_data = generar_pdf(nombre_doc, dni_limpio, path_plantilla)
                        
                        # Generar botones de descarga dinámicos instantáneos
                        st.download_button(
                            label=f"📥 Descargar PDF: {fecha_evento}",
                            data=pdf_data,
                            file_name=f"Constancia_{dni_limpio}_{fecha_evento}.pdf",
                            mime="application/pdf",
                            key=f"dl_{fecha_evento}"
                        )
                
                if not alguna_seleccionada:
                    st.warning("⚠️ Debe tildar al menos una constancia para descargar.")

        else:
            st.error("El DNI ingresado no se encuentra registrado en ninguna de las nóminas.")
else:
    st.warning("⚠️ No se detectaron carpetas de eventos en la carpeta 'eventos/'.")
