import pandas as pd
from datetime import datetime
import streamlit as st
from io import BytesIO

st.title("📊 Verificador de Llegadas Tarde")
st.write("Sube tu archivo Excel con los registros de huella para analizar quién llegó tarde o no tiene registro.")

archivo = st.file_uploader("📎 Cargar archivo Excel", type=["xlsx"])

# Turnos definidos por franja horaria
turnos = {
    "07:06": ("07:06", "07:40"),
    "08:06": ("08:06", "08:40"),
    "13:06": ("13:06", "13:40"),
    "14:06": ("14:06", "14:40"),
    "19:06": ("19:06", "19:40"),
}

def identificar_turno(hora):
    for inicio_str, (inicio, fin) in turnos.items():
        h_inicio = datetime.strptime(inicio, "%H:%M").time()
        h_fin = datetime.strptime(fin, "%H:%M").time()
        if h_inicio <= hora.time() <= h_fin:
            return inicio_str, h_inicio
    return None, None

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
                llego_tarde = hora_llegada.time() > hora_turno
                resultado.append({
                    "Nombre": nombre,
                    "Fecha": row['Fecha'],
                    "Hora Llegada": hora_llegada.time(),
                    "Turno": turno_detectado,
                    "Llego Tarde": "Sí" if llego_tarde else "No"
                })

        resultado_df = pd.DataFrame(resultado)

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
                "Llego Tarde": "Sin registro"
            })

        faltantes_df = pd.DataFrame(faltantes)
        reporte = pd.concat([resultado_df, faltantes_df], ignore_index=True)
        reporte = reporte.sort_values(by=["Fecha", "Nombre"])

        st.success("✅ Análisis completado. Aquí tienes los resultados:")
        st.dataframe(reporte)

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
