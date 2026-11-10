# BuildEstimator Web

Aplikasi web Streamlit untuk estimasi kebutuhan material rumah tinggal maksimal 2 lantai.

## Jalankan lokal
1. Install Python 3.10+.
2. Buka terminal pada folder proyek.
3. Jalankan:
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```
4. Buka alamat lokal yang ditampilkan Streamlit (umumnya http://localhost:8501).

## Deploy ke Streamlit Community Cloud
1. Unggah seluruh isi folder ini ke repository GitHub.
2. Buka https://share.streamlit.io/ dan hubungkan GitHub.
3. Pilih repository, branch, dan file `app.py`.
4. Deploy.

## Database
Gunakan `data/template_database_material.xlsx`. Sheet `KOEFISIEN_BAHAN` dan `HARGA` dapat diisi, lalu diunggah melalui sidebar aplikasi.

## Catatan teknis
- Koefisien bawaan masih asumsi prototipe dari program sumber. Verifikasi dengan AHSP/HSD yang berlaku.
- Edit database pada aplikasi disimpan dalam sesi aktif; untuk penyimpanan permanen lintas sesi diperlukan database/server persisten.
- Estimasi ini bukan pengganti desain struktur, gambar kerja, survei, atau pemeriksaan ahli.
