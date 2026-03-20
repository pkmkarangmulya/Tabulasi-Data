import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import os

# --- SETTING HALAMAN ---
st.set_page_config(page_title="Tabulasi Lengkongjaya Pro + Scoring", layout="wide")

DB_FILE = 'database_tabulasi_fix.csv'

# --- FUNGSI ANALISIS SKOR KESEHATAN ---
def analisis_skor(bb, tb, gds, td):
    skor_pesan = []
    status_warna = "normal" # default
    
    # 1. Analisis IMT (BB/TB^2)
    try:
        tb_m = float(tb) / 100
        imt = float(bb) / (tb_m * tb_m)
        if imt < 18.5: skor_pesan.append("⚠️ Kekurangan Berat Badan")
        elif 18.5 <= imt <= 25: skor_pesan.append("✅ Berat Badan Ideal")
        else: 
            skor_pesan.append("🚨 Obesitas/Kelebihan Berat Badan")
            status_warna = "warning"
    except: pass

    # 2. Analisis Gula Darah (GDS)
    try:
        g = float(gds)
        if g >= 200: 
            skor_pesan.append("🚨 GDS Tinggi (Risiko Diabetes)")
            status_warna = "danger"
        elif g < 70: skor_pesan.append("⚠️ Hipoglikemia (Gula Rendah)")
    except: pass

    # 3. Analisis Tekanan Darah (TD)
    try:
        sistolik = int(td.split('/')[0])
        if sistolik >= 140: 
            skor_pesan.append("🚨 Hipertensi (Tekanan Darah Tinggi)")
            status_warna = "danger"
    except: pass

    return " | ".join(skor_pesan) if skor_pesan else "Belum Ada Data Klinis", status_warna

def clean_uploaded_data(df):
    for i in range(min(10, len(df))):
        row_values = df.iloc[i].astype(str).values
        if any('NAMA' in val for val in row_values) or any('NIK' in val for val in row_values):
            df.columns = df.iloc[i]
            df = df.iloc[i+1:].reset_index(drop=True)
            break
    df = df.loc[:, df.columns.notna()]
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df

# --- INTERFACE ---
st.title("🏥 Sistem Tabulasi & Skor Kesehatan CKG")
st.caption("Versi Terpadu: Analisis IMT, GDS, & Hipertensi")

with st.sidebar:
    st.header("⚙️ Database")
    uploaded_file = st.file_uploader("Upload Master CSV", type=["csv"])
    if uploaded_file:
        raw_df = pd.read_csv(uploaded_file, sep=None, engine='python')
        df_cleaned = clean_uploaded_data(raw_df)
        df_cleaned.to_csv(DB_FILE, index=False, sep=';')
        st.success("Database Berhasil Disinkronkan!")

if os.path.exists(DB_FILE):
    df = pd.read_csv(DB_FILE, sep=';')
    tab1, tab2, tab3 = st.tabs(["📝 Input & Skor", "🔍 Filter Data", "📈 Evaluasi & Grafik"])

    # --- TAB 1: INPUT DENGAN TANGGAL FLEKSIBEL ---
    with tab1:
        with st.form("form_pemeriksaan"):
            st.subheader("Form Pemeriksaan Pasien")
            c1, c2, c3 = st.columns(3)
            with c1:
                f_nama = st.text_input("Nama Lengkap").upper()
                f_nik = st.text_input("NIK")
                # Tanggal lahir tanpa batasan (dari tahun 1900 sampai hari ini)
                f_tgl = st.date_input("Tanggal Lahir", 
                                     min_value=date(1900, 1, 1), 
                                     max_value=date.today(),
                                     value=date(1990, 1, 1))
            with c2:
                f_jk = st.selectbox("Jenis Kelamin", ["L", "P"])
                f_bb = st.number_input("Berat Badan (kg)", min_value=0.0, step=0.1)
                f_tb = st.number_input("Tinggi Badan (cm)", min_value=0.0, step=0.1)
            with c3:
                f_td = st.text_input("Tensi (Contoh: 120/80)")
                f_gds = st.number_input("Gula Darah (mg/dL)", min_value=0)
                f_alamat = st.text_input("Kampung/Alamat")

            if st.form_submit_button("Analisis & Simpan"):
                skor_hasil, warna = analisis_skor(f_bb, f_tb, f_gds, f_td)
                umur = date.today().year - f_tgl.year
                
                new_data = pd.DataFrame([{
                    "NO": len(df)+1, "NAMA": f_nama, "NO NIK": f"'{f_nik}",
                    "TANGGAL LAHIR": f_tgl.strftime("%d/%m/%Y"),
                    "L": "TRUE" if f_jk == "L" else "FALSE",
                    "P": "TRUE" if f_jk == "P" else "FALSE",
                    "BB": f_bb, "TB": f_tb, "TD": f_td, "GDS": f_gds,
                    "STATUS KESEHATAN": skor_hasil, "UMUR": f"{umur} Tahun",
                    "ALAMAT LENGKAP": f_alamat
                }])
                
                df = pd.concat([df, new_data], ignore_index=True)
                df.to_csv(DB_FILE, index=False, sep=';')
                st.success(f"Hasil Analisis: {skor_hasil}")
                st.rerun()

    # --- TAB 2: FILTER MULTI-HEADER ---
    with tab2:
        st.subheader("Pencarian & Filter")
        all_cols = df.columns.tolist()
        selected_cols = st.multiselect("Pilih Kolom Tampil", all_cols, default=["NAMA", "NO NIK", "UMUR", "STATUS KESEHATAN"])
        
        # Filter Dinamis
        f_df = df
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            search_nama = st.text_input("Cari Nama")
            if search_nama: f_df = f_df[f_df['NAMA'].str.contains(search_nama.upper(), na=False)]
        with c_f2:
            if "STATUS KESEHATAN" in df.columns:
                unique_status = df["STATUS KESEHATAN"].unique().tolist()
                sel_status = st.multiselect("Filter Status Kesehatan", unique_status)
                if sel_status: f_df = f_df[f_df["STATUS KESEHATAN"].isin(sel_status)]

        st.dataframe(f_df[selected_cols], use_container_width=True)

    # --- TAB 3: EVALUASI ---
    with tab3:
        st.subheader("Statistik Kesehatan Warga")
        if "STATUS KESEHATAN" in df.columns:
            # Hitung risiko
            risiko_count = df[df['STATUS KESEHATAN'].str.contains("🚨", na=False)].shape[0]
            st.metric("Total Warga Berisiko Tinggi", risiko_count)
            
            fig = px.pie(df, names="STATUS KESEHATAN", title="Proporsi Status Kesehatan")
            st.plotly_chart(fig)
else:
    st.info("Sidebar: Silakan upload file CSV master untuk memulai.")
