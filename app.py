import pandas as pd
from datetime import datetime
import streamlit as st
from io import BytesIO

# Configuración visual de la app
st.set_page_config(page_title="Verificador de Llegadas Tarde", page_icon="⏰", layout="centered")

# Título y logo
st.markdown("<h1 style='text-align: center; color: navy;'>⏰ Verificador de Llegadas Tarde</h1>", unsafe_allow_html=True)
st.image("logo.png", width=180)  # Asegúrate de tener "logo.png" en el mismo repositorio

# Instrucciones
st.info("""
Bienvenido al sistema de control de asistencias por franja horaria.

📎 Sube tu archivo Excel con los registros de huella.  
✅ El sistema detecta automáticamente quién llegó temprano, a tiempo, tarde o no tiene registro.
""")

# Carga de archivo
archivo = st.file_uploader("📁 Cargar archivo Excel", type=["xlsx"])

# Turnos por franja horaria (con tolerancia)
turnos = {
    "07:00": ("07:06", "07:40"),
    "08:00": ("08:06", "08:40"),
    "13:00": ("13:06", "13:40"),
    "14:00": ("14:06", "14:40"),
    "19:00": ("19:06", "19:40"),
}

# Función para identificar turno
def identificar_turno(hora):
    for inicio_str, (inicio, fin) in turnos.items():
        h_inicio = datetime.strptime(inicio, "%H:%M").time()
        h_fin = datetime.strptime(fin, "%H:%M").time()
        if h_inicio <= hora.time() <= h_fin:
            return inicio_str, h_inicio
    return None, None

# Función para aplicar colores al estado
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

# Procesamiento del archivo
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

        # Buscar personas sin primer registro
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
        reporte = pd.concat([resultado_df, faltantes_df], ignore_index=True)
        reporte = reporte.sort_values(by=["Fecha", "Nombre"])

        # Mostrar tabla con estilo
        st.success("✅ Análisis completado. Aquí tienes los resultados:")
        styled = reporte.style.applymap(resaltar_estado, subset=["Estado"])
        st.dataframe(styled, use_container_width=True)

        # Descargar como Excel
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
