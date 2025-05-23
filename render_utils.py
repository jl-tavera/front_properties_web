from collections import Counter
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium


def render_map(df: pd.DataFrame, key: str):
    """Renderiza el mapa con marcadores de apartamentos con mejor estilo visual."""
    df[["lat", "lon"]] = pd.DataFrame(df["coordinates"].tolist(), index=df.index)
    df = df.dropna(subset=["lat", "lon"])
    if df.empty:
        st.warning("No hay coordenadas válidas para mostrar en el mapa.")
        return

    center = [df["lat"].mean(), df["lon"].mean()]
    m = folium.Map(
        location=center,
        zoom_start=13,
        control_scale=True,
        tiles="CartoDB Voyager"  # 💡 Mejor alternativa visual a CartoDB Positron
    )

    for _, row in df.iterrows():
        price = f"${int(row.get('price', 0)):,}".replace(",", " ")
        popup_html = f"""
        <div style="font-family: 'Poppins', sans-serif; font-size: 14px;">
            <strong>ID: {row.get('id', 'Apto')}</strong><br>
            💰 <strong>Precio:</strong> {price} COP<br>
            🛏️ <strong>Habitaciones:</strong> {row.get('bedrooms', '?')}<br>
            📐 <strong>Área:</strong> {row.get('area', '?')} m²
        </div>
        """
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"Apto {row.get('id', '')}",
            icon=folium.Icon(color="gray", icon="home", prefix="fa")  # ✅ gris moderno
        ).add_to(m)

    # 🔄 Ajuste de tamaño automático al ancho del contenedor
    with st.container():
        st_folium(m, width=None, height=500, key=key)


def render_results(df: pd.DataFrame):
    """Renderiza los resultados de los apartamentos como tarjetas."""
    st.markdown("Aquí tienes algunos apartamentos recomendados:")
    for row in df.itertuples():
        with st.container():
            st.markdown("---")
            cols = st.columns([2, 1])
            with cols[0]:
                st.markdown(f"""
                **🏠 ID: {row.id}**  
                💰 **Precio:** {row.price:,} COP  
                🛏️ **Habitaciones:** {row.bedrooms}  
                🛁 **Baños:** {row.bathrooms}  
                📐 **Área:** {row.area} m²  
                📍 **Ubicación:** {row.coordinates[0]:.4f}, {row.coordinates[1]:.4f}
                """)
            with cols[1]:
                st.link_button("Ver apartamento", row.link)

    st.markdown("Si quieres mas información pon los digitos del ID en el chat o usa el comando **comparar** para obtener un análisis comparativo!")

def render_comparison_report(df: pd.DataFrame):
    st.subheader("📊 Análisis de los apartamentos encontrados")

    # --- Basic summary
    st.markdown("📋 Resumen general")
    avg_price = df["price"].mean()
    avg_area = df["area"].mean()
    most_common_stratum = df["stratum"].mode()[0] if not df["stratum"].isna().all() else "N/A"

    st.markdown(f"""
    - Número total de apartamentos: **{len(df)}**
    - Precio promedio: **${avg_price:,.0f} COP**
    - Área promedio: **{avg_area:.1f} m²**
    - Estrato más frecuente: **{most_common_stratum}**
    - Agencias distintas: **{df['agency'].nunique()}**
    """)

     # --- Area vs Price scatter
    st.markdown("📐 Relación entre Área y Precio")
    st.scatter_chart(df, x="area", y="price",use_container_width=True)

    # --- Bedrooms distribution
    st.markdown("🛏️ Número de habitaciones")
    st.bar_chart(df["bedrooms"].value_counts().sort_index())

    # --- Bathrooms distribution
    st.markdown("🛁 Número de baños")
    st.bar_chart(df["bathrooms"].value_counts().sort_index())

    # --- Stratum distribution
    st.markdown("🎖️ Distribución por estrato")
    st.bar_chart(df["stratum"].value_counts().sort_index())


    # --- Facilities analysis
    st.markdown("🛠️ Amenidades más comunes")
    if "facilities" in df.columns:
        all_facilities = sum(df["facilities"], [])  # flatten list of lists
        facility_counts = Counter(all_facilities).most_common(10)
        fac_df = pd.DataFrame(facility_counts, columns=["Amenidad", "Cantidad"])
        st.dataframe(fac_df)