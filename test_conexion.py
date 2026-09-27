import streamlit as st
from supabase import create_client

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

st.write("URL:", url)
st.write("Key (primeros 20):", key[:20])

supabase = create_client(url, key)

# Intentar listar todas las tablas accesibles
try:
    # Probamos con nombres comunes
    for nombre in ["series", "Series", "Series Final - Series Final", "anime", "anime_history"]:
        try:
            res = supabase.table(nombre).select("*").limit(1).execute()
            st.success(f"✅ Tabla encontrada: '{nombre}' → {len(res.data)} registros visibles")
        except Exception as e:
            st.warning(f"❌ '{nombre}' → {str(e)[:100]}")
except Exception as e:
    st.error(f"Error general: {e}")