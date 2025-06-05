import streamlit as st
import pandas as pd
import io
from datetime import datetime, time

# Configuración de la página
st.set_page_config(
    page_title="Verificador de Asistencia",
    page_icon="⏰",
    layout="centered"
)

# Encabezado y bienvenida
st.markdown("<h1 style='text-align: center; color: navy;'>⏰ Verificador de Llegadas Tarde</h1>", unsafe_allow_html=True)

st.info("""
Bienvenido al sistema de control de asistencias por franja horaria.

📁 Solo necesitas subir el archivo Excel de los registros de huella dactilar.

✅ El sistema detectará automáticamente si los empleados llegaron tarde o no tienen registro, según su franja horaria.

""")

# Puedes mostrar un logo si tienes uno (descomenta la línea siguiente si lo subes)
# st.image("logo.png", width=200)

# Subida del archivo
archivo = st.file_uploader("📁 Selecciona el archivo de huellas (.xlsx)", type=["xlsx"])

if archivo is not None:
    df = pd.read_excel(archivo)

    # Limpiar y asegurar formato de columnas
    df.columns = df.columns.str.strip()
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    df['Hora Llegada'] = pd.to_datetime(df['Hora Llegada'], errors='coerce').dt.time

    # Definir rangos de entrada por turno
    franjas = {
        "7:06 AM": time(7, 0),
        "8:06 AM": time(8, 0),
        "1:06 PM": time(13, 0),
        "2:06 PM": time(14, 0),
        "7:06 PM": time(19, 0),
    }

    tolerancia_minutos = 40

    # Función para asignar franja
    def asignar_turno(hora):
        if pd.isnull(hora):
            return None
        for nombre_turno, hora_turno in franjas.items():
            inicio = (datetime.combine(datetime.today(), hora_turno)).time()
            fin = (datetime.combine(datetime.today(), hora_turno).replace(minute=hora_turno.minute + tolerancia_minutos)).time()
            if hora >= inicio and hora <= fin:
                return nombre_turno
        return "Fuera de Rango"

    df['Turno'] = df['Hora Llegada'].apply(asignar_turno)

    def llego_tarde(row):
        if pd.isnull(row['Hora Llegada']):
            return "Sin Registro"
        if row['Turno'] in franjas:
            hora_referencia = franjas[row['Turno']]
            return "Tarde" if row['Hora Llegada'] > hora_referencia else "A Tiempo"
        return "Fuera de Rango"

    df['Tardanza'] = df.apply(llego_tarde, axis=1)

    # Mostrar tabla
    st.subheader("📄 Reporte de Asistencias")
    st.dataframe(df)

    # Descargar resultado
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte')
    st.download_button(
        label="📥 Descargar informe de asistencia",
        data=output.getvalue(),
        file_name='reporte_asistencia.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
else:
    st.warning("Por favor, sube un archivo Excel para continuar.")