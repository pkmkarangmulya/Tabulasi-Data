import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import os
import io

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Tabulasi Lengkongjaya Auto-Cleaner", layout="wide")

DB_FILE = 'database_tabulasi_fix.csv'

# --- 1. FUNGSI AUTO-CLEANER (MESIN PEMBERSIH DATA) ---
def auto_clean_csv(uploaded_file):
    try:
        # Membaca file mentah
        raw_bytes = uploaded_file.read()
        # Deteksi encoding dan baca ke dataframe
        df_raw = pd.read_csv(io.BytesIO(raw_bytes), sep=None, engine='python', header=None)
        
        # A. Mencari letak Header (Baris yang mengandung 'NAMA' atau 'NO NIK')
        header_row_index = None
        for i in range(len(df_raw)):
            row_values = [str(x).upper() for x in df_raw.iloc[i].values]
            if 'NAMA' in row_values or 'NO NIK' in row_values:
                header_row_index = i
                break
        
        if header_row_index is None:
            return None, "Gagal menemukan judul kolom (NAMA/NIK). Pastikan file benar."

        # B. Potong baris di atas header
        df_clean = df_raw.iloc[header_row_index:].copy()
        df_clean.columns = df_clean.iloc[0] # Set baris tersebut jadi header
        df_clean = df_clean.iloc[1:].reset_index(drop=True) # Hapus baris header dari isi data

        # C. Gabungkan sub-header jika ada (Baris L/P atau RT/RW yang terpisah)
        # Jika baris pertama setelah header banyak NaN, kemungkinan itu sub-header
        if df_clean.iloc[0].isnull().sum() > (len(df_clean.columns) / 2):
            df_clean = df_clean.iloc[1:].reset_index(drop=True)

        # D. Bersihkan Nama Kolom (Hapus Unnamed dan NaN)
        df_clean.columns = [str(col) if pd.notna(col) else f"Unnamed_{i}" for i, col in enumerate(df_clean.columns)]
        df_clean = df_clean.loc[:, ~df_clean.columns.str.contains('Unnamed')]

        # E. Hapus baris sampah (Baris yang NAMANYA kosong)
        if 'NAMA' in df_clean.columns:
            df_clean = df_clean.dropna(subset=['NAMA'])
            df_clean = df_clean[df_clean['NAMA'].str.strip() != ""]

        return df_clean, "Sukses"
    except Exception as e:
        return None, f"Error saat membersihkan: {str(e)}"

# --- 2. FUNGSI INISIALISASI ---
def init_db():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        cols = ["NO", "NAMA", "NO NIK", "TANGGAL LAHIR", "UMUR", "STATUS KESEHATAN", "RT/RW", "TD", "GDS", "BB", "TB"]
        pd.DataFrame(columns=cols).to_csv(DB_FILE, index=False, sep=';')

# --- 3. LOGIKA SKORING ---
def hitung_skor(bb, tb, gds, td):
    res = []
    try:
        if float(tb) > 0:
            imt = float(bb) / ((float(tb)/100)**2)
            if imt > 25: res.append("🚨 Obesitas")
            elif imt < 18.5: res.append("⚠️ Kurang BB")
        if float(gds) >= 200: res.append("🚨 GDS Tinggi")
        sis = int(str(td).split('/')[0])
        if sis >= 140: res.append("🚨 Hipertensi")
    except: pass
    return " | ".join(res) if res else "✅ Normal"

# --- MAIN APP ---
init_db()

with st.sidebar:
    st.header("⚙️ Smart Uploader")
    st.write("Upload file yang berantakan di sini, sistem akan merapikan otomatis.")
    up = st.file_uploader("Upload CSV Tabulasi", type=["csv"])
    
    if up:
        with st.spinner("Sedang membersihkan data..."):
            df_cleaned, msg = auto_clean_csv(up)
            if df_cleaned is not None:
                df_cleaned.to_csv(DB_FILE, index=False, sep=';')
                st.success("✅ Database Bersih Berhasil Disimpan!")
                st.rerun()
            else:
                st.error(msg)

    if st.button("🗑️ Kosongkan Database"):
        os.remove(DB_FILE)
        st.rerun()

st.title("🏥 Dashboard Kesehatan Lengkongjaya")
df = pd.read_csv(DB_FILE, sep=';')

t1, t2, t3 = st.tabs(["📝 Input Baru", "🔍 Database Master", "📊 Analisis"])

with t1:
    with st.form("f_in"):
        st.subheader("Form Tambah Data")
        c1, c2, c3 = st.columns(3)
        with c1:
            nama = st.text_input("Nama Pasien").upper()
            nik = st.text_input("NIK")
            tgl = st.date_input("Tanggal Lahir", min_value=date(1900,1,1), value=date(1990,1,1))
        with c2:
            rt_rw = st.text_input("RT/RW")
            bb = st.number_input("BB (kg)", 0.0)
            tb = st.number_input("TB (cm)", 0.0)
        with c3:
            td = st.text_input("Tensi (120/80)")
            gds = st.number_input("GDS", 0)
        
        if st.form_submit_button("Simpan & Analisis"):
            if nama:
                skor = hitung_skor(bb, tb, gds, td)
                thn = date.today().year - tgl.year
                row = pd.DataFrame([{
                    "NO": len(df)+1, "NAMA": nama, "NO NIK": f"'{nik}",
                    "TANGGAL LAHIR": tgl.strftime("%d/%m/%Y"), "UMUR": f"{thn} Thn",
                    "STATUS KESEHATAN": skor, "RT/RW": rt_rw, "TD": td, "GDS": gds, "BB": bb, "TB": tb
                }])
                df = pd.concat([df, row], ignore_index=True)
                df.to_csv(DB_FILE, index=False, sep=';')
                st.success(f"Tersimpan! Status: {skor}")
                st.rerun()

with t2:
    st.subheader("Database Hasil Auto-Clean")
    cari = st.text_input("Cari Nama/NIK")
    d_v = df
    if cari:
        d_v = d_v[d_v['NAMA'].str.contains(cari.upper(), na=False) | d_v['NO NIK'].astype(str).str.contains(cari)]
    st.dataframe(d_v, use_container_width=True)
    st.download_button("📥 Download Master CSV", d_v.to_csv(index=False, sep=';'), "master_data_clean.csv")

with t3:
    if not df.empty:
        c_a1, c_a2 = st.columns(2)
        with c_a1:
            fig = px.pie(df, names="STATUS KESEHATAN", title="Proporsi Kesehatan Warga")
            st.plotly_chart(fig)
        with c_a2:
            if "RT/RW" in df.columns:
                fig2 = px.histogram(df, x="RT/RW", title="Partisipasi per Wilayah")
                st.plotly_chart(fig2)
