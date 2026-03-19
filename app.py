import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import os

# --- SETTING HALAMAN ---
st.set_page_config(page_title="Tabulasi Lengkongjaya Pro", layout="wide")

DB_FILE = 'database_tabulasi_fix.csv'

# --- 1. FUNGSI TEMPLATE DATABASE (Mencegah EmptyDataError) ---
def init_database():
    columns = [
        "NO", "NAMA", "NO NIK", "TANGGAL LAHIR", "L", "P", 
        "UMUR", "TD", "GDS", "BB", "TB", "STATUS KESEHATAN", 
        "ALAMAT LENGKAP", "RT/RW"
    ]
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        df_empty = pd.DataFrame(columns=columns)
        df_empty.to_csv(DB_FILE, index=False, sep=';')

# --- 2. FUNGSI MEMBERSIHKAN HEADER DARI UPLOAD ---
def clean_header(df):
    for i in range(min(15, len(df))):
        row = df.iloc[i].astype(str).values
        if 'NAMA' in [str(x).upper() for x in row]:
            df.columns = df.iloc[i]
            df = df.iloc[i+1:].reset_index(drop=True)
            break
    df = df.loc[:, df.columns.notna()]
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df

# --- 3. FUNGSI SKOR KESEHATAN ---
def hitung_skor(bb, tb, gds, td):
    catatan = []
    try:
        if float(tb) > 0:
            imt = float(bb) / ((float(tb)/100)**2)
            if imt > 25: catatan.append("🚨 Obesitas")
            elif imt < 18.5: catatan.append("⚠️ Kurang BB")
        if float(gds) >= 200: catatan.append("🚨 GDS Tinggi")
        sistolik = int(str(td).split('/')[0])
        if sistolik >= 140: catatan.append("🚨 Hipertensi")
    except: pass
    return " | ".join(catatan) if catatan else "✅ Normal"

# --- MAIN APP ---
init_database() # Jalankan inisialisasi di awal

with st.sidebar:
    st.header("⚙️ Database")
    uploaded = st.file_uploader("Upload Master CSV", type=["csv"])
    if uploaded:
        raw = pd.read_csv(uploaded, sep=None, engine='python')
        cleaned = clean_header(raw)
        cleaned.to_csv(DB_FILE, index=False, sep=';')
        st.success("Database Berhasil Diperbarui!")
        st.rerun()
    
    if st.button("🗑️ Reset Database"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        init_database()
        st.rerun()

st.title("🏥 Sistem Informasi Kesehatan Lengkongjaya")
df = pd.read_csv(DB_FILE, sep=';')

tab1, tab2, tab3 = st.tabs(["📝 Input & Skor", "🔍 Filter Data", "📈 Analisis"])

# --- TAB 1: INPUT DATA ---
with tab1:
    with st.form("form_input", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            nama = st.text_input("Nama").upper()
            nik = st.text_input("NIK")
            tgl_lhr = st.date_input("Tanggal Lahir", min_value=date(1900,1,1), max_value=date.today(), value=date(1990,1,1))
        with c2:
            jk = st.selectbox("JK", ["L", "P"])
            alamat = st.text_input("Alamat")
            rt_rw = st.text_input("RT/RW")
        with c3:
            bb = st.number_input("BB (kg)", min_value=0.0)
            tb = st.number_input("TB (cm)", min_value=0.0)
            td = st.text_input("Tensi (120/80)")
            gds = st.number_input("GDS", min_value=0)
        
        if st.form_submit_button("Simpan & Analisis"):
            if nama:
                skor_txt = hitung_skor(bb, tb, gds, td)
                umur = date.today().year - tgl_lhr.year
                new_row = pd.DataFrame([{
                    "NO": len(df)+1, "NAMA": nama, "NO NIK": f"'{nik}",
                    "TANGGAL LAHIR": tgl_lhr.strftime("%d/%m/%Y"),
                    "L": "TRUE" if jk == "L" else "FALSE", "P": "TRUE" if jk == "P" else "FALSE",
                    "UMUR": f"{umur} Tahun", "TD": td, "GDS": gds, "BB": bb, "TB": tb,
                    "STATUS KESEHATAN": skor_txt, "ALAMAT LENGKAP": alamat, "RT/RW": rt_rw
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_csv(DB_FILE, index=False, sep=';')
                st.success(f"Data Tersimpan! Status: {skor_txt}")
                st.rerun()

# --- TAB 2: FILTER DATA ---
with tab2:
    st.subheader("Filter & Tabel Data")
    f_nama = st.text_input("Cari Nama/NIK")
    d_view = df
    if f_nama:
        d_view = d_view[d_view['NAMA'].str.contains(f_nama.upper(), na=False) | d_view['NO NIK'].str.contains(f_nama, na=False)]
    
    st.dataframe(d_view, use_container_width=True)
    st.download_button("📥 Download CSV", d_view.to_csv(index=False, sep=';'), "data_kesehatan.csv")

# --- TAB 3: ANALISIS ---
with tab3:
    if not df.empty:
        c_a1, c_a2 = st.columns(2)
        with c_a1:
            st.write("**Status Kesehatan**")
            fig = px.pie(df, names="STATUS KESEHATAN")
            st.plotly_chart(fig, use_container_width=True)
        with c_a2:
            st.write("**Partisipasi per RT/RW**")
            fig2 = px.histogram(df, x="RT/RW")
            st.plotly_chart(fig2, use_container_width=True)
