import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Validación de Sostenibilidad", layout="wide")

st.title("🌿 Aplicación Interactiva - Validación de Indicadores de Sostenibilidad")
st.markdown("""
Esta aplicación permite ingresar los **indicadores de sostenibilidad** de los **4 ejes** del modelo de urbanismo ecológico.  
Calcula automáticamente los puntajes, porcentajes por eje y la **calificación final (A–E)**.
""")

default_indicators = {
    "Eje 1 - Compacidad y funcionalidad": [
        {"indicador": "Compacidad absoluta", "ref": "≥ 50%", "puntos_max": 20},
        {"indicador": "Compacidad corregida", "ref": "≥ 50%", "puntos_max": 20},
        {"indicador": "Accesibilidad del viario", "ref": "≥ 90% longitud calles con acera ≥ 3m", "puntos_max": 60},
        {"indicador": "Espacio viario destinado al peatón", "ref": "≥ 60% del viario peatonal", "puntos_max": 50},
        {"indicador": "Proporción de la calle (H/D)", "ref": "H/D < 2", "puntos_max": 30}
    ],
    "Eje 2 - Urbanismo ecológico": [
        {"indicador": "Espacio verde por habitante", "ref": "> 10 m²/hab", "puntos_max": 100},
        {"indicador": "Calidad del aire", "ref": "PM2.5 < 10 µg/m³ (OMS)", "puntos_max": 40},
        {"indicador": "Confort acústico", "ref": "< 55 dB(A)", "puntos_max": 30},
        {"indicador": "Biodiversidad urbana", "ref": "≥ 3 especies por 100 m²", "puntos_max": 20},
        {"indicador": "Índice biótico del suelo", "ref": "> 25%", "puntos_max": 20}
    ],
    "Eje 3 - Metabolismo urbano": [
        {"indicador": "Eficiencia energética de edificios", "ref": "Estándar A o superior", "puntos_max": 40},
        {"indicador": "Gestión de residuos", "ref": "≥ 60% reciclaje", "puntos_max": 35},
        {"indicador": "Consumo de agua", "ref": "≤ 100 L/hab·día", "puntos_max": 35},
        {"indicador": "Energías renovables", "ref": "≥ 20% cobertura", "puntos_max": 30}
    ],
    "Eje 4 - Cohesión y habitabilidad": [
        {"indicador": "Cohesión social - participación", "ref": "Programas activos ≥ 80%", "puntos_max": 30},
        {"indicador": "Complejidad urbana - diversidad de usos", "ref": "≥ 3 usos por manzana", "puntos_max": 30},
        {"indicador": "Espacio de estancia por habitante", "ref": "≥ 10 m²/hab", "puntos_max": 50},
        {"indicador": "Servicios y equipamientos", "ref": "≥ 80% a < 500 m", "puntos_max": 40}
    ]
}

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Eje", "Indicador", "Puntos máx", "Puntos alcanzados", "Comentarios"])

st.sidebar.header("➕ Agregar Indicador")

eje_sel = st.sidebar.selectbox("Selecciona el Eje", list(default_indicators.keys()))
indicadores_eje = [i["indicador"] for i in default_indicators[eje_sel]]
indic_sel = st.sidebar.selectbox("Indicador", indicadores_eje)
pmax = next(i["puntos_max"] for i in default_indicators[eje_sel] if i["indicador"] == indic_sel)
ref_sel = next(i["ref"] for i in default_indicators[eje_sel] if i["indicador"] == indic_sel)

puntos_max = st.sidebar.number_input("Puntos máximos", value=float(pmax))
puntos_alc = st.sidebar.number_input("Puntos alcanzados", value=0.0)
coment = st.sidebar.text_area("Comentarios", value=f"Referencia: {ref_sel}")

if st.sidebar.button("Agregar a tabla"):
    nuevo = {"Eje": eje_sel, "Indicador": indic_sel, "Puntos máx": puntos_max, "Puntos alcanzados": puntos_alc, "Comentarios": coment}
    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([nuevo])], ignore_index=True)
    st.sidebar.success("✅ Indicador agregado correctamente")

st.subheader("📋 Tabla de Indicadores")
st.dataframe(st.session_state.data, use_container_width=True)

if not st.session_state.data.empty:
    df = st.session_state.data.copy()
    df["Puntos máx"] = pd.to_numeric(df["Puntos máx"], errors="coerce").fillna(0)
    df["Puntos alcanzados"] = pd.to_numeric(df["Puntos alcanzados"], errors="coerce").fillna(0)

    resumen = df.groupby("Eje").agg({"Puntos máx": "sum", "Puntos alcanzados": "sum"}).reset_index()
    resumen["% alcanzado"] = resumen.apply(lambda r: (r["Puntos alcanzados"] / r["Puntos máx"] * 100) if r["Puntos máx"] > 0 else 0, axis=1)
    resumen["Peso (%)"] = 25
    resumen["Contribución (sobre 100)"] = resumen["% alcanzado"] * resumen["Peso (%)"] / 100
    total = round(resumen["Contribución (sobre 100)"].sum(), 1)

    if total >= 90:
        letra = "A (Excelente)"
    elif total >= 70:
        letra = "B (Notable)"
    elif total >= 50:
        letra = "C (Suficiente)"
    elif total >= 25:
        letra = "D (Insuficiente)"
    else:
        letra = "E (Muy insuficiente)"

    st.subheader("📊 Resultados por Eje")
    st.table(resumen)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Calificación final (%)", f"{total} %")
    with col2:
        st.metric("Nivel", letra)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Indicadores")
        resumen.to_excel(writer, index=False, sheet_name="Resumen por Eje")
    st.download_button(
        label="📥 Descargar resultados (Excel)",
        data=buffer.getvalue(),
        file_name="Validacion_Sostenibilidad.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Agrega indicadores desde el panel lateral para calcular resultados.")

st.markdown("---")
st.caption("💡 Desarrollado para evaluación de sostenibilidad urbana con base en los 4 ejes del modelo de Urbanismo Ecológico.")
