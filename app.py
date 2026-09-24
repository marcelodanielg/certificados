import io
import os
import base64
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
import streamlit as st
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN DE PÁGINA ---
X_TEXTO, Y_TEXTO, TAM_LETRA = 300, 265, 20

st.set_page_config(
    page_title="Constancias de Asistencia", 
    page_icon="📜",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. DISEÑO RESPONSIVO PROFESIONAL (PC Y MÓVIL) ---
st.markdown(
    """
    <style>
    /* Ocultar elementos de Streamlit */
    #MainMenu, footer, header, .stDeployButton, #stDecoration { display: none !important; }
    
    /* Contenedor principal adaptable: Elegante en PC, completo en Celular */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 750px !important; /* Evita que se estire demasiado en monitores grandes */
    }
    
    .stApp { background-color: #f0f2f5; }

    /* Encabezado Principal */
    .header-container {
        text-align: center;
        padding: 18px;
        margin-bottom: 15px;
        background: linear-gradient(135deg, #1b4965 0%, #2b5876 100%);
        border-radius: 12px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .header-container h1 {
        margin: 0;
        font-size: 24px;
        font-weight: 700;
        font-family: system-ui, -apple-system, sans-serif;
    }
    .header-container p {
        margin: 5px 0 0 0;
        font-size: 13px;
        opacity: 0.9;
    }

    /* Tarjetas de instrucciones y resultados */
    .tarjeta-bienvenida {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px 20px;
        border: 1px solid #e2e8f0;
        margin-bottom: 15px;
        font-size: 14px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .pasos-lista {
        margin: 5px 0 0 0;
        padding-left: 20px;
        color: #4a5568;
        font-size: 13px;
        line-height: 1.4;
    }

    /* Formulario limpio y moderno */
    div[data-testid="stForm"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 2px solid #1b4965;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.03);
    }
    div[data-testid="stForm"] label {
        font-size: 15px !important;
        font-weight: bold !important;
        color: #1b4965 !important;
    }
    div[data-testid="stForm"] input {
        font-size: 16px !important;
        padding: 10px !important;
        border-radius: 6px !important;
    }

    /* Tarjeta de evento encontrado */
    .tarjeta-evento {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-left: 5px solid #1b4965;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    /* Botones destacados */
    .stButton>button, .stDownloadButton>button {
        background-color: #1b4965 !important;
        color: #ffffff !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        padding: 12px !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100% !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: background-color 0.2s;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background-color: #112d40 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- 3. CARGA GLOBAL Y CENTRALIZADA DE TODOS LOS EVENTOS ---
@st.cache_data(ttl=3600)
def cargar_todos_los_eventos():
    """Escanea automáticamente la carpeta 'eventos' y consolida todas las fechas."""
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


def generar_imagen_previa(nombre, dni, path_plantilla):
    img = Image.open(path_plantilla).convert("RGB")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("Arial.ttf", TAM_LETRA + 10)
    except Exception:
        font = ImageFont.load_default()

    texto = f"{nombre.upper()} - DNI: {dni}"
    draw.text((X_TEXTO, Y_TEXTO), texto, fill="black", anchor="mm")
    return img


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


def mostrar_visor_interactivo(pil_image):
    buffered = io.BytesIO()
    pil_image.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://unpkg.com/@panzoom/panzoom@4.5.1/dist/panzoom.min.js"></script>
        <style>
            * {{ box-sizing: border-box; }}
            body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; }}
            .panzoom-container {{
                width: 100%; max-width: 100%; height: auto; aspect-ratio: 4 / 3;
                border-radius: 8px; overflow: hidden; background: #e2e8f0;
                touch-action: none; display: flex; justify-content: center; align-items: center;
            }}
            #cert-img {{ width: 100%; height: 100%; object-fit: contain; }}
        </style>
    </head>
    <body>
        <div class="panzoom-container">
            <img id="cert-img" src="data:image/png;base64,{img_b64}" alt="Certificado">
        </div>
        <script>
            const elem = document.getElementById('cert-img');
            const panzoom = Panzoom(elem, {{ maxScale: 4, minScale: 1, contain: 'outside' }});
            elem.parentElement.addEventListener('wheel', panzoom.zoomWithWheel);
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=240)


# --- 4. INTERFAZ DE USUARIO ---
st.markdown(
    """
    <div class='header-container'>
        <h1>📜 Constancias de Asistencia</h1>
        <p>Ministerio de Educación — Sistema de Emisión Digital</p>
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
                <li>El sistema buscará automáticamente en todas las capacitaciones y le mostrará sus constancias disponibles para descargar.</li>
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
            st.success(f"¡Se encontraron **{len(encontrados)}** constancia(s) asociada(s) al DNI {dni_limpio}!")
            
            for item in encontrados:
                nombre_doc = item["nombre"]
                fecha_evento = item["evento"]
                path_plantilla = item["path_plantilla"]

                pdf_data = generar_pdf(nombre_doc, dni_limpio, path_plantilla)
                img_prev = generar_imagen_previa(nombre_doc, dni_limpio, path_plantilla)

                st.markdown(
                    f"""
                    <div class='tarjeta-evento'>
                        📅 <b>Evento / Fecha:</b> {fecha_evento}<br>
                        👤 <b>Docente:</b> {nombre_doc}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                mostrar_visor_interactivo(img_prev)

                st.download_button(
                    label=f"📥 Descargar PDF ({fecha_evento})",
                    data=pdf_data,
                    file_name=f"Constancia_{dni_limpio}_{fecha_evento}.pdf",
                    mime="application/pdf",
                    key=f"btn_{fecha_evento}"
                )
                st.markdown("<br>", unsafe_allow_html=True)

        else:
            st.error("El DNI ingresado no se encuentra registrado en ninguna de las nóminas de asistencia disponibles.")
else:
    st.warning("⚠️ No se detectaron carpetas de eventos configuradas en el repositorio (dentro de la carpeta 'eventos/').")
