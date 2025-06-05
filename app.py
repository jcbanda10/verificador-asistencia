import pandas as pd
from datetime import datetime
import streamlit as st
from io import BytesIO

# Configuración general de la app
st.set_page_config(page_title="Verificador de Llegadas Tarde", page_icon="⏰", layout="centered")

# Estilo personalizado (sin fondo blanco)
st.markdown("""
    <style>
        h1 {
            color: #0b5394;
            text-align: center;
            margin-bottom: 0;
        }
        .logo-container {
            display: flex;
            justify-content: center;
            margin-top: -20px;
            margin-bottom: 20px;
        }
        .stButton>button {
            background-color: #0b5394;
            color: white;
            border-radius: 10px;
            padding: 0.5em 1em;
            font-size: 1rem;
        }
        .stButton>button:hover {
            background-color: #073763;
        }
        .stFileUploader {
            border: 2px dashed #0b5394;
            border-radius: 10px;
            padding: 1em;
            background-color: #f3f7fc;
        }
    </style>
""", unsafe_allow_html=True)

# Título y logo
st.markdown("<h1>⏰ Verificador de Llegadas Tarde</h1>", unsafe_allow_html=True)
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
st.image("Logo.png", width=280)
st.markdown('</div>', unsafe_allow_html=True)

# Descripción
st.info("""
📎 Sube tu archivo Excel con los registros de huella.  
El sistema detecta automáticamente quién llegó **temprano**, **a tiempo**, **tarde** o no tiene **registro**.
""")

# Subida del archivo
archivo = st.file_uploader("📁 Cargar archivo Excel", type=["xlsx"])

# Turnos y márgenes de tolerancia
turnos = {
    "07:00": ("07:06", "07:40"),
    "08:00": ("08:06", "08:40"),
    "13:00": ("13:06", "13:40"),
    "14:00": ("14:06", "14:40"),
    "19:00": ("19:06", "19:40"),
}

# Detectar franja de entrada
def identificar_turno(hora):
    for inicio_str, (inicio, fin) in turnos.items():
        h_inicio = datetime.strptime(inicio, "%H:%M").time()
        h_fin = datetime.strptime(fin, "%H:%M").time()
        if h_inicio <= hora.time() <= h_fin:
            return inicio_str, h_inicio
    return None, None

# Colorear la columna de Estado
def resaltar_estado(val):
    color = ""
    if val == "Temprano":
        color = "background-color: lightgreen"
    elif val == "A tiempo":
        color = "background-color: khaki"
    elif val == "Tarde":
        color = "background-color: lightcoral"
    elif val == "Sin registro":
        color = "background-color: lightgray"
    return color

# Procesar el archivo
if archivo:
    try:
        df = pd.read_excel(archivo)
        df = df[df['Evento'] == 'Desbloqueo de huellas']
        df = df.dropna(subset=['Nombre', 'Hora'])
        df['Hora'] = pd.to_datetime(df['Hora'])
        df['Fecha'] = df['Hora'].dt.date

        primeras = df.sort_values('Hora').groupby(['Nombre', 'Fecha']).first().reset_index()

        resultado = []
        for _, row in primeras.iterrows():
            nombre = row['Nombre']
            hora_llegada = row['Hora']
            turno_detectado, hora_turno = identificar_turno(hora_llegada)
            if turno_detectado:
                if hora_llegada.time() < hora_turno:
                    estado = "Temprano"
                elif hora_llegada.time() <= datetime.strptime(turno_detectado, "%H:%M").time():
                    estado = "A tiempo"
                else:
                    estado = "Tarde"
                resultado.append({
                    "Nombre": nombre,
                    "Fecha": row['Fecha'],
                    "Hora Llegada": hora_llegada.time(),
                    "Turno": turno_detectado,
                    "Estado": estado
                })

        resultado_df = pd.DataFrame(resultado)

        # Ver quién no tiene registro
        nombres_todos = df['Nombre'].dropna().unique()
        nombres_con_llegada = resultado_df['Nombre'].unique()
        nombres_sin_llegada = set(nombres_todos) - set(nombres_con_llegada)
        fecha_unica = primeras['Fecha'].unique()[0] if not primeras.empty else datetime.today().date()

        faltantes = []
        for nombre in nombres_sin_llegada:
            faltantes.append({
                "Nombre": nombre,
                "Fecha": fecha_unica,
                "Hora Llegada": None,
                "Turno": None,
                "Estado": "Sin registro"
            })

        faltantes_df = pd.DataFrame(faltantes)

        # Unir resultados
        reporte = pd.concat([resultado_df, faltantes_df], ignore_index=True)
        reporte = reporte.sort_values(by=["Fecha", "Nombre"])

        # Mostrar resultados con color
        st.success("✅ Análisis completado. Aquí tienes los resultados:")
        styled = reporte.style.applymap(resaltar_estado, subset=["Estado"])
        st.dataframe(styled, use_container_width=True)

        # Exportar como Excel
        output = BytesIO()
        reporte.to_excel(output, index=False, engine='openpyxl')
        st.download_button(
            label="⬇️ Descargar reporte en Excel",
            data=output.getvalue(),
            file_name="reporte_llegadas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Error procesando el archivo: {e}")
