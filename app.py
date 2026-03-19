import streamlit as st
import pandas as pd
from datetime import date
import os

# Konfigurasi Judul Halaman
st.set_page_config(page_title="Sistem Input Data Digital", layout="centered")

st.title("📝 Form Penginputan Data")
st.write("Isi formulir di bawah ini untuk menyimpan data ke database lokal.")

# Membuat Form Input
with st.form(key='input_form'):
    col1, col2 = st.columns(2)
    
    with col1:
        nama = st.text_input("Nama Lengkap")
        kategori = st.selectbox("Kategori", ["Administrasi", "Kesehatan", "Operasional", "Lainnya"])
    
    with col2:
        jumlah = st.number_input("Jumlah/Nilai", min_value=0, step=1)
        tanggal = st.date_input("Tanggal Kejadian", date.today())
    
    catatan = st.text_area("Catatan Tambahan")
    
    submit_button = st.form_submit_button(label='Simpan Data')

# Logika Penyimpanan Data
if submit_button:
    new_data = {
        "Tanggal_Input": [date.today()],
        "Nama": [nama],
        "Kategori": [kategori],
        "Jumlah": [jumlah],
        "Tanggal_Kejadian": [tanggal],
        "Catatan": [catatan]
    }
    
    df = pd.DataFrame(new_data)
    
    # Simpan ke CSV (Menambah data baru di bawah data lama)
    file_name = "database_input.csv"
    if not os.path.isfile(file_name):
        df.to_csv(file_name, index=False)
    else:
        df.to_csv(file_name, mode='a', index=False, header=False)
        
    st.success(f"Data milik {nama} berhasil disimpan!")
    st.balloons()

# Menampilkan Data yang Sudah Masuk
if st.checkbox("Tampilkan Riwayat Data"):
    if os.path.isfile("database_input.csv"):
        data_lama = pd.read_csv("database_input.csv")
        st.dataframe(data_lama)
    else:
        st.info("Belum ada data yang tersimpan.")
