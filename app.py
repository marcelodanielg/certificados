import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import os

# Configuración de la página
st.set_page_config(page_title="Generador de Certificados", page_icon="🎓")

# Estilo para mejorar la apariencia
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎓 Descarga tu Certificado")
st.write("Ingresa tu DNI para obtener tu certificado personalizado.")

# --- FUNCIÓN DE GENERACIÓN ---
def generar_certificado(nombre_texto, dni_texto):
    # 1. Abrir la plantilla y forzar modo RGB
    try:
        img = Image.open("plantilla.png").convert("RGB")
    except Exception as e:
        st.error(f"Error: No se encontró 'plantilla.png' en el repositorio. {e}")
        return None

    draw = ImageDraw.Draw(img)

    # 2. Configurar fuentes
    # Intentamos cargar arial.ttf desde la carpeta raíz del repo
    font_path = "./arial.ttf"
    
    try:
        # Aumentamos tamaño a 200/250 para que sea visible en altas resoluciones
        if os.path.exists(font_path):
            font_nombre = ImageFont.truetype(font_path, 250) 
            font_dni = ImageFont.truetype(font_path, 120)
        else:
            st.warning("Archivo arial.ttf no detectado, usando fuente básica.")
            font_nombre = font_dni = ImageFont.load_default()
    except:
        font_nombre = font_dni = ImageFont.load_default()

    # 3. UBICACIONES (Basadas en tus coordenadas)
    # 'mm' significa que el centro del texto estará en esa coordenada (mejor para centrar nombres)
    pos_nombre = (2351, 1575)
    pos_dni = (5203, 1575)

    # 4. Dibujar los textos
    # Color negro: (0, 0, 0). Si no se ve, prueba (255, 0, 0) para rojo de prueba.
    draw.text(pos_nombre, str(nombre_texto), font=font_nombre, fill=(0, 0, 0), anchor="mm")
    draw.text(pos_dni, str(dni_texto), font=font_dni, fill=(0, 0, 0), anchor="mm")

    # 5. Convertir a bytes para descarga
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- LÓGICA DE BÚSQUEDA ---
@st.cache_data # Para que no recargue el Excel en cada clic
def cargar_datos():
    try:
        df = pd.read_excel("asistentes.xlsx", dtype={'DNI': str})
        df['DNI'] = df['DNI'].str.strip()
        df['Nombre'] = df['Nombre'].str.strip()
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo Excel: {e}")
        return None

df = cargar_datos()

if df is not None:
    # Interfaz de usuario
    dni_usuario = st.text_input("Escribe tu DNI (sin puntos ni espacios):")

    if dni_usuario:
        # Buscar en el DataFrame
        datos = df[df['DNI'] == dni_usuario]
        
        if not datos.empty:
            nombre_asistente = datos.iloc[0]['Nombre']
            dni_asistente = datos.iloc[0]['DNI']
            
            st.success(f"✅ ¡Hola {nombre_asistente}! Tu certificado está listo.")
            
            # Generar imagen
            archivo_cert = generar_certificado(nombre_asistente, dni_asistente)
            
            if archivo_cert:
                # Mostrar vista previa
                st.image(archivo_cert, caption="Vista previa de tu certificado", use_container_width=True)
                
                # Botón de descarga
                st.download_button(
                    label="⬇️ Descargar Certificado (PNG)",
                    data=archivo_cert,
                    file_name=f"Certificado_{dni_asistente}.png",
                    mime="image/png"
                )
        else:
            st.error("❌ El DNI ingresado no se encuentra en nuestra lista.")
else:
    st.info("Esperando base de datos...")

st.divider()
st.caption("Sistema de certificación automática - Generado con Streamlit")

