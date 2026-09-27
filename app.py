import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# ---------- CONFIGURACIÓN ----------
st.set_page_config(page_title="Mi Historial de Anime", layout="wide", page_icon="📺")
st.title("📺 Mi Historial de Anime")

# ---------- CONEXIÓN ----------
@st.cache_resource
def get_connection():
    return psycopg2.connect(st.secrets["DATABASE_URL"])

def query(sql, params=None, fetch=True):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            if fetch and cur.description:
                return pd.DataFrame(cur.fetchall())
            conn.commit()
            return None
    except Exception as e:
        conn.rollback()
        raise e

# ---------- CARGAR DATOS ----------
@st.cache_data(ttl=60)
def cargar_datos():
    return query("SELECT * FROM series ORDER BY structured_date DESC")

try:
    df = cargar_datos()
except Exception as e:
    st.error(f"❌ Error conectando a la base de datos: {e}")
    st.stop()

# ---------- MÉTRICAS ----------
col1, col2, col3, col4 = st.columns(4)
col1.metric("📚 Total de series", len(df))
col2.metric("❤️ Favoritas", int(df['is_favorite'].sum()))
col3.metric("✅ Terminadas", len(df[df['status'] == 'Terminada']))
col4.metric("🔄 Rewatches", len(df[df['status'] == 'Rewatch']))

# ---------- FILTROS EN SIDEBAR ----------
st.sidebar.header("🔍 Filtros")

df['year'] = pd.to_datetime(df['structured_date']).dt.year
años = ["Todos"] + sorted(df['year'].dropna().unique().tolist(), reverse=True)
año_sel = st.sidebar.selectbox("Año", años)

estados = ["Todos"] + sorted(df['status'].dropna().unique().tolist())
estado_sel = st.sidebar.selectbox("Estado", estados)

solo_fav = st.sidebar.checkbox("Solo favoritas")
busqueda = st.sidebar.text_input("Buscar por nombre")

df_filt = df.copy()
if año_sel != "Todos":
    df_filt = df_filt[df_filt['year'] == año_sel]
if estado_sel != "Todos":
    df_filt = df_filt[df_filt['status'] == estado_sel]
if solo_fav:
    df_filt = df_filt[df_filt['is_favorite'] == True]
if busqueda:
    df_filt = df_filt[df_filt['series_name'].str.contains(busqueda, case=False, na=False)]

st.subheader(f"📋 Resultados ({len(df_filt)} series)")

st.dataframe(
    df_filt[['series_name', 'episode_season', 'status', 'is_favorite', 'structured_date', 'comment']],
    use_container_width=True,
    hide_index=True
)

# ---------- AÑADIR NUEVA SERIE ----------
st.sidebar.markdown("---")
st.sidebar.header("➕ Añadir serie")

with st.sidebar.form("nueva_serie", clear_on_submit=True):
    nombre = st.text_input("Nombre de la serie*")
    episodio = st.text_input("Episodio/Temporada")
    date_orig = st.text_input("Fecha original (texto)")
    comentario = st.text_area("Comentario")
    estado_nuevo = st.selectbox("Estado", ["Continuando", "Terminada", "Rewatch"])
    favorita = st.checkbox("Favorita")
    fecha = st.date_input("Fecha estructurada", value=datetime.today())

    enviar = st.form_submit_button("Guardar")

    if enviar and nombre:
        query("""
            INSERT INTO series
            (series_name, episode_season, date_original, comment, status, is_favorite, structured_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (nombre, episodio, date_orig, comentario, estado_nuevo, favorita, fecha), fetch=False)
        st.cache_data.clear()
        st.success(f"✅ '{nombre}' añadida")
        st.rerun()

# ---------- EDITAR REGISTRO ----------
st.markdown("---")
st.subheader("✏️ Editar una serie")

nombres = sorted(df['series_name'].unique().tolist())
serie_sel = st.selectbox("Selecciona una serie", nombres)

if serie_sel:
    filas = df[df['series_name'] == serie_sel]
    st.write(f"Hay **{len(filas)}** registro(s) para esta serie.")

    idx = st.selectbox(
        "Selecciona el registro",
        filas.index.tolist(),
        format_func=lambda i: f"{filas.loc[i, 'structured_date']} - {filas.loc[i, 'status']} - {filas.loc[i, 'episode_season']}"
    )
    row = df.loc[idx]

    with st.form("editar"):
        nuevo_estado = st.selectbox(
            "Estado",
            ["Continuando", "Terminada", "Rewatch"],
            index=["Continuando", "Terminada", "Rewatch"].index(row['status']) if row['status'] in ["Continuando", "Terminada", "Rewatch"] else 0
        )
        nueva_fav = st.checkbox("Favorita", value=bool(row['is_favorite']))
        nuevo_comentario = st.text_area("Comentario", value=row['comment'] or "")
        nueva_fecha = st.date_input("Fecha", value=pd.to_datetime(row['structured_date']).date())

        actualizar = st.form_submit_button("Actualizar")
        eliminar = st.form_submit_button("🗑️ Eliminar registro", type="secondary")

        if actualizar:
            query("""
                UPDATE series
                SET status = %s, is_favorite = %s, comment = %s, structured_date = %s
                WHERE id = %s
            """, (nuevo_estado, nueva_fav, nuevo_comentario, nueva_fecha, int(row['id'])), fetch=False)
            st.cache_data.clear()
            st.success("✅ Actualizado")
            st.rerun()

        if eliminar:
            query("DELETE FROM series WHERE id = %s", (int(row['id']),), fetch=False)
            st.cache_data.clear()
            st.warning("🗑️ Registro eliminado")
            st.rerun()