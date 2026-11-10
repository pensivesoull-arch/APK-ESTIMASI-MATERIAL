"""Mesin perhitungan BuildEstimator, diturunkan dari aplikasi Python pengguna."""
import math
import pandas as pd

# %% Cell 1: Import library
# Semua library ini sudah tersedia di Google Colab, tidak perlu pip install.
import math
import pandas as pd


# %% Cell 2: Validasi input
# Semua pengecekan input dikumpulkan di sini. Jika input salah, program
# melempar InputError dan perhitungan TIDAK dilanjutkan.

class InputError(ValueError):
    """Kesalahan input pengguna (pesannya ditampilkan apa adanya)."""

def angka(nilai, nama, boleh_nol=False):
    """Ubah input jadi angka. Huruf, kosong, negatif (dan nol) ditolak."""
    try:
        x = float(str(nilai).strip().replace(",", "."))   # koma desimal diterima
    except (TypeError, ValueError):
        raise InputError(f"Error: {nama} harus berupa angka.")
    if math.isnan(x) or math.isinf(x):
        raise InputError(f"Error: {nama} harus berupa angka yang valid.")
    if x < 0:
        raise InputError(f"Error: {nama} tidak boleh bernilai negatif.")
    if x == 0 and not boleh_nol:
        raise InputError(f"Error: {nama} harus bernilai lebih besar dari 0.")
    return x

def bulat(nilai, nama, boleh_nol=False):
    """Bilangan bulat positif (atau nol jika boleh_nol=True)."""
    x = angka(nilai, nama, boleh_nol)
    if abs(x - round(x)) > 1e-9:
        raise InputError(f"Error: {nama} harus bilangan bulat.")
    return int(round(x))

def pilihan(nilai, nama, daftar):
    if nilai not in daftar:
        raise InputError(f"Error: {nama} harus salah satu dari: {', '.join(daftar)}.")
    return nilai

def n(d, kunci, boleh_nol=False):
    """Ambil angka dari dict input d[kunci] sambil divalidasi."""
    if kunci not in d:
        raise InputError(f"Error: data '{kunci}' belum diisi.")
    return angka(d[kunci], kunci.replace("_", " "), boleh_nol)

def b(d, kunci, boleh_nol=False):
    if kunci not in d:
        raise InputError(f"Error: data '{kunci}' belum diisi.")
    return bulat(d[kunci], kunci.replace("_", " "), boleh_nol)

PILIHAN = {
    "pondasi":      ["batu_kali", "footplat"],
    "dinding":      ["bata_merah", "bata_ringan"],
    "rangka_atap":  ["baja_ringan", "kayu"],
    "penutup_atap": ["genteng_keramik", "spandek"],
    "keramik":      ["30x30", "40x40", "60x60", "custom"],
}

def validasi_proyek(p):
    """Periksa identitas proyek; kembalikan dict bersih (angka sudah float/int)."""
    q = dict(p)
    q["nama"] = str(p.get("nama", "")).strip()
    if not q["nama"]:
        raise InputError("Error: nama proyek harus diisi.")
    q["pemilik"] = str(p.get("pemilik", "")).strip() or "-"
    q["lantai"] = b(p, "lantai")
    if q["lantai"] not in (1, 2):
        raise InputError("Error: jumlah lantai maksimal 2 (pilih 1 atau 2).")
    for k in ("panjang", "lebar", "tinggi1"):
        q[k] = n(p, k)
    q["tinggi2"] = n(p, "tinggi2") if q["lantai"] == 2 else 0.0
    for k, daftar in PILIHAN.items():
        pilihan(p.get(k), k.replace("_", " "), daftar)
    if q["keramik"] == "custom":
        q["keramik_p_cm"] = n(p, "keramik_p_cm")
        q["keramik_l_cm"] = n(p, "keramik_l_cm")
    return q

def ukuran_keramik(P):
    """Ukuran keramik dalam meter (p, l) dan labelnya."""
    if P["keramik"] == "custom":
        return P["keramik_p_cm"] / 100, P["keramik_l_cm"] / 100, f"{P['keramik_p_cm']:g}x{P['keramik_l_cm']:g}"
    a, c = P["keramik"].split("x")
    return int(a) / 100, int(c) / 100, P["keramik"]

# %% Cell 3: Database koefisien, waste, dan harga
# Database ini TERPISAH dari mesin perhitungan. Nilai di bawah adalah ASUMSI
# PROTOTIPE supaya program bisa dijalankan. Ganti dengan koefisien AHSP dan
# harga Mas Petruk (lihat cell 'Muat data resmi' di bagian bawah).

ASUMSI, RESMI = "ASUMSI PROTOTIPE", "REFERENSI RESMI"
SUMBER0 = "Belum diisi dari AHSP / Mas Petruk"

# kode, pekerjaan, satuan_pekerjaan, material, spesifikasi, satuan_material, koefisien
_DB = [
 # --- Beton struktur (per m3 beton) ---
 ("BETON", "Beton struktur", "m3", "Semen Portland", "PC", "kg", 371),
 ("BETON", "Beton struktur", "m3", "Pasir", "Pasir beton", "m3", 0.50),
 ("BETON", "Beton struktur", "m3", "Kerikil", "Kerikil beton", "m3", 0.70),
 ("BETON", "Beton struktur", "m3", "Air", "Air kerja", "liter", 215),
 # --- Tulangan (kg per m3 beton, tiap elemen beda) ---
 ("BESI_SLOOF",   "Tulangan sloof",    "m3", "Besi beton", "Dia. 10 mm", "kg", 150),
 ("BESI_KOLOM",   "Tulangan kolom",    "m3", "Besi beton", "Dia. 10 mm", "kg", 180),
 ("BESI_BALOK",   "Tulangan balok",    "m3", "Besi beton", "Dia. 10 mm", "kg", 160),
 ("BESI_PELAT",   "Tulangan pelat",    "m3", "Besi beton", "Dia. 8 mm",  "kg", 90),
 ("BESI_TANGGA",  "Tulangan tangga",   "m3", "Besi beton", "Dia. 8 mm",  "kg", 110),
 ("BESI_FOOTPLAT","Tulangan footplat", "m3", "Besi beton", "Dia. 12 mm", "kg", 120),
 # --- Persiapan & tanah ---
 ("LANTAI_KERJA", "Beton lantai kerja", "m3", "Semen Portland", "PC", "kg", 230),
 ("LANTAI_KERJA", "Beton lantai kerja", "m3", "Pasir", "Pasir beton", "m3", 0.55),
 ("LANTAI_KERJA", "Beton lantai kerja", "m3", "Kerikil", "Kerikil beton", "m3", 0.80),
 ("URUG_PASIR", "Urugan pasir", "m3", "Pasir", "Pasir urug", "m3", 1.2),
 ("URUG_TANAH", "Urugan tanah kembali", "m3", "Tanah urug", "Tanah galian", "m3", 1.0),
 # --- Pondasi batu kali ---
 ("PASANGAN_BATU_KALI", "Pasangan batu kali", "m3", "Batu kali", "Batu belah", "m3", 1.2),
 ("PASANGAN_BATU_KALI", "Pasangan batu kali", "m3", "Semen Portland", "PC", "kg", 163),
 ("PASANGAN_BATU_KALI", "Pasangan batu kali", "m3", "Pasir", "Pasir pasang", "m3", 0.52),
 # --- Dinding ---
 ("DINDING_BATA_MERAH", "Pasangan bata merah", "m2", "Bata merah", "1/2 bata", "buah", 70),
 ("DINDING_BATA_MERAH", "Pasangan bata merah", "m2", "Semen Portland", "PC", "kg", 11.5),
 ("DINDING_BATA_MERAH", "Pasangan bata merah", "m2", "Pasir", "Pasir pasang", "m3", 0.043),
 ("DINDING_BATA_RINGAN", "Pasangan bata ringan", "m2", "Bata ringan", "60x20x10 cm", "buah", 8.33),
 ("DINDING_BATA_RINGAN", "Pasangan bata ringan", "m2", "Mortar perekat", "Thin bed", "kg", 4.0),
 # --- Lantai ---
 ("KERAMIK_SPESI", "Spesi pasang keramik", "m2", "Semen Portland", "PC", "kg", 9.0),
 ("KERAMIK_SPESI", "Spesi pasang keramik", "m2", "Pasir", "Pasir pasang", "m3", 0.045),
 ("KERAMIK_NAT", "Nat keramik", "m2", "Nat keramik", "Semen nat", "kg", 0.3),
 # --- Atap ---
 ("ATAP_RANGKA_BAJA", "Rangka baja ringan", "m2", "Rangka baja ringan", "Kanal C + reng", "kg", 5.0),
 ("ATAP_RANGKA_KAYU", "Rangka kayu", "m2", "Kayu rangka", "Kaso + reng", "m3", 0.035),
 ("ATAP_AKSESORIS_BAJA", "Sekrup rangka", "m2", "Sekrup", "Self drilling", "buah", 7),
 ("ATAP_AKSESORIS_KAYU", "Paku rangka", "m2", "Paku", "5-10 cm", "kg", 0.05),
 ("PENUTUP_GENTENG_KERAMIK", "Penutup genteng", "m2", "Genteng keramik", "Standar", "buah", 25),
 ("PENUTUP_SPANDEK", "Penutup spandek", "m2", "Spandek", "0,4 mm", "m2", 1.0),
 ("NOK_GENTENG_KERAMIK", "Nok genteng", "m", "Genteng nok", "Keramik", "buah", 3),
 ("NOK_SPANDEK", "Nok spandek", "m", "Nok spandek", "0,4 mm", "m", 1.0),
 # --- Finishing ---
 ("PLESTER", "Plesteran", "m2", "Semen Portland", "PC", "kg", 6.24),
 ("PLESTER", "Plesteran", "m2", "Pasir", "Pasir plester", "m3", 0.024),
 ("ACIAN", "Acian", "m2", "Semen Portland", "PC", "kg", 3.25),
 ("CAT_DINDING", "Cat dinding", "m2", "Cat dinding", "Interior", "kg", 0.2),
 ("CAT_PLAFON", "Cat plafon", "m2", "Cat plafon", "Interior", "kg", 0.15),
 ("GYPSUM", "Plafon gypsum", "m2", "Gypsum board", "9 mm 120x240", "lembar", 0.3472),
 ("UNIT_PINTU", "Pintu", "unit", "Pintu", "Kusen + daun", "unit", 1),
 ("UNIT_JENDELA", "Jendela", "unit", "Jendela", "Kusen + daun", "unit", 1),
 # --- Utilitas ---
 ("PIPA_AIR_BERSIH", "Pipa air bersih", "m", "Pipa air bersih", "PVC", "m", 1),
 ("PIPA_AIR_KOTOR", "Pipa air kotor", "m", "Pipa air kotor", "PVC", "m", 1),
 ("KABEL_LISTRIK", "Kabel listrik", "m", "Kabel listrik", "NYM", "m", 1),
 ("TITIK_LAMPU", "Titik lampu", "unit", "Titik lampu", "Standar", "unit", 1),
 ("STOP_KONTAK", "Stopkontak", "unit", "Stopkontak", "Standar", "unit", 1),
 ("CLOSET", "Closet", "unit", "Closet", "Standar", "unit", 1),
 ("WASTAFEL", "Wastafel", "unit", "Wastafel", "Standar", "unit", 1),
 ("KRAN", "Kran air", "unit", "Kran air", "Standar", "unit", 1),
]
KOLOM_DB = ["kode", "pekerjaan", "satuan_pekerjaan", "material", "spesifikasi",
            "satuan_material", "koefisien", "sumber", "status"]
DB = pd.DataFrame([r + (SUMBER0, ASUMSI) for r in _DB], columns=KOLOM_DB)

# Faktor waste per material (bisa diubah). Material yang tidak tercantum = 0.
WASTE = {"Bata merah": 0.05, "Bata ringan": 0.05, "Keramik lantai": 0.10,
         "Genteng keramik": 0.05, "Genteng nok": 0.05, "Spandek": 0.05,
         "Gypsum board": 0.10, "Pipa air bersih": 0.10, "Pipa air kotor": 0.10,
         "Kabel listrik": 0.10, "Cat dinding": 0.05, "Cat plafon": 0.05}

# Tabel harga bahan (isi dari Mas Petruk -> HSD -> Bahan). Awalnya kosong.
HARGA = (DB[["material", "spesifikasi", "satuan_material"]]
         .drop_duplicates().rename(columns={"satuan_material": "satuan"})
         .reset_index(drop=True))
HARGA["harga_min"] = float("nan")
HARGA["harga_max"] = float("nan")
HARGA["sumber"] = "Belum diisi"
MODE_HARGA = "rata-rata"       # pilihan: "min", "max", "rata-rata"

def ubah_koefisien(kode, material, nilai, spesifikasi=None, sumber="Diubah manual"):
    """Ubah satu koefisien di database. Nilai harus > 0."""
    nilai = angka(nilai, "koefisien")
    m = (DB["kode"] == kode) & (DB["material"] == material)
    if spesifikasi:
        m &= DB["spesifikasi"] == spesifikasi
    if not m.any():
        raise InputError(f"Error: kode '{kode}' dengan material '{material}' tidak ditemukan.")
    DB.loc[m, ["koefisien", "sumber", "status"]] = [nilai, sumber, RESMI]
    return int(m.sum())

def ubah_waste(material, nilai):
    """Waste dalam pecahan (0,05 = 5 persen). Tidak boleh negatif."""
    WASTE[material] = angka(nilai, f"waste {material}", boleh_nol=True)

def muat_koefisien_csv(path):
    """Timpa koefisien dari CSV berkolom: kode, material, spesifikasi, koefisien, sumber.
    Baris yang kolom 'sumber'-nya kosong / masih default dilewati (dianggap belum diisi)."""
    d = pd.read_csv(path)
    dimuat = 0
    for r in d.itertuples():
        sumber = "" if pd.isna(r.sumber) else str(r.sumber).strip()
        if not sumber or sumber == SUMBER0:
            continue
        ubah_koefisien(r.kode, r.material, r.koefisien, r.spesifikasi, sumber)
        dimuat += 1
    return dimuat

def muat_harga_csv(path):
    """Isi harga dari CSV berkolom: material, spesifikasi, harga_min, harga_max, sumber."""
    global HARGA
    d = pd.read_csv(path)
    kunci = ["material", "spesifikasi"]
    HARGA = HARGA.drop(columns=["harga_min", "harga_max", "sumber"]).merge(
        d[kunci + ["harga_min", "harga_max", "sumber"]], on=kunci, how="left")
    HARGA["sumber"] = HARGA["sumber"].fillna("Belum diisi")
    return len(d)

# %% Cell 4: Penampung hasil
NAMA_MODUL = {1: "1. Persiapan & Tanah", 2: "2. Pondasi", 3: "3. Struktur Beton",
              4: "4. Dinding", 5: "5. Lantai", 6: "6. Atap", 7: "7. Finishing",
              8: "8. Utilitas"}
DISKRIT = {"buah", "lembar", "unit"}     # material yang dibulatkan ke atas

class Hasil:
    """Menampung hasil semua modul: daftar volume dan daftar material."""
    def __init__(self):
        self.vol, self.mat, self.info = [], [], {}

    def volume(self, no, uraian, jumlah, satuan):
        self.vol.append({"no": no, "modul": NAMA_MODUL[no], "uraian": uraian,
                         "jumlah": jumlah, "satuan": satuan})

    def material(self, no, kode, uraian, qty, satuan_qty):
        """Kalikan volume/luas dengan semua koefisien milik 'kode' di database."""
        sub = DB[DB["kode"] == kode]
        if sub.empty:
            raise InputError(f"Error: koefisien '{kode}' tidak ada di database.")
        for r in sub.itertuples():
            if r.satuan_pekerjaan != satuan_qty:
                raise InputError(f"Error: satuan '{kode}' di database ({r.satuan_pekerjaan}) "
                                 f"tidak cocok dengan satuan hitungan ({satuan_qty}).")
            self._tambah(no, kode, uraian, qty, satuan_qty, r.material,
                         r.spesifikasi, r.satuan_material, r.koefisien)

    def langsung(self, no, uraian, qty, satuan_qty, material, spek, satuan, koef):
        """Untuk koefisien yang dihitung dari rumus (misalnya jumlah keping keramik)."""
        self._tambah(no, "(rumus)", uraian, qty, satuan_qty, material, spek, satuan, koef)

    def _tambah(self, no, kode, uraian, qty, satuan_qty, material, spek, satuan, koef):
        w = WASTE.get(material, 0.0)
        self.mat.append({"no": no, "modul": NAMA_MODUL[no], "uraian": uraian,
                         "kode": kode, "volume": qty, "satuan_volume": satuan_qty,
                         "material": material, "spesifikasi": spek,
                         "koefisien": koef, "waste": w,
                         "kebutuhan": qty * koef * (1 + w), "satuan": satuan})

# %% Cell 5: Rumus modul 1 sampai 4
def modul1(P, A, H, vol_pondasi):
    """Persiapan & tanah. vol_pondasi (m3) dikurangkan dari urugan kembali."""
    a, M = A["m1"], 1
    H.volume(M, "Luas area bangunan (proyeksi)", P["panjang"] * P["lebar"], "m2")
    pj, lb, dl = n(a, "panjang_galian"), n(a, "lebar_galian"), n(a, "kedalaman_galian")
    ts, tk = n(a, "tebal_urug_pasir"), n(a, "tebal_lantai_kerja")
    if ts + tk >= dl:
        raise InputError("Error: tebal urug pasir + lantai kerja harus lebih kecil dari kedalaman galian.")
    v_gal, v_pasir, v_lk = pj * lb * dl, pj * lb * ts, pj * lb * tk
    v_urug = v_gal - vol_pondasi - v_pasir - v_lk
    if v_urug < 0:
        raise InputError("Error: volume pondasi + urug pasir + lantai kerja melebihi volume galian. "
                         "Periksa dimensi galian.")
    H.volume(M, "Galian tanah pondasi", v_gal, "m3")
    H.volume(M, "Urugan pasir", v_pasir, "m3")
    H.material(M, "URUG_PASIR", "Urugan pasir", v_pasir, "m3")
    H.volume(M, "Beton lantai kerja", v_lk, "m3")
    H.material(M, "LANTAI_KERJA", "Beton lantai kerja", v_lk, "m3")
    H.volume(M, "Urugan tanah kembali", v_urug, "m3")
    H.material(M, "URUG_TANAH", "Urugan tanah kembali", v_urug, "m3")

def modul2(P, A, H):
    """Pondasi: HANYA jenis yang dipilih di identitas proyek yang dihitung."""
    a, M = A["m2"], 2
    if P["pondasi"] == "batu_kali":
        q = a["batu_kali"]
        vol = (n(q, "lebar_atas") + n(q, "lebar_bawah")) / 2 * n(q, "tinggi") * n(q, "panjang_total")
        H.volume(M, "Pondasi batu kali (trapesium)", vol, "m3")
        H.material(M, "PASANGAN_BATU_KALI", "Pondasi batu kali", vol, "m3")
    else:
        q = a["footplat"]
        vol = b(q, "jumlah_titik") * n(q, "sisi_x") * n(q, "sisi_y") * n(q, "tebal")
        H.volume(M, "Pondasi footplat", vol, "m3")
        H.material(M, "BETON", "Beton footplat", vol, "m3")
        H.material(M, "BESI_FOOTPLAT", "Tulangan footplat", vol, "m3")
    H.info["vol_pondasi"] = vol

# kunci, nama, lantai minimal, kode tulangan
ELEMEN = [("sloof", "Sloof", 1, "BESI_SLOOF"),
          ("kolom1", "Kolom lantai 1", 1, "BESI_KOLOM"),
          ("kolom2", "Kolom lantai 2", 2, "BESI_KOLOM"),
          ("balok1", "Balok lantai 1", 1, "BESI_BALOK"),
          ("balok2", "Balok lantai 2", 2, "BESI_BALOK"),
          ("pelat", "Pelat lantai dua", 2, "BESI_PELAT")]

def modul3(P, A, H):
    """Struktur beton: volume = panjang x lebar x tinggi x jumlah."""
    a, M = A["m3"], 3
    for kunci, nama, lt_min, kode_besi in ELEMEN:
        if P["lantai"] < lt_min:
            continue
        q = a["elemen"][kunci]
        vol = n(q, "panjang") * n(q, "lebar") * n(q, "tinggi") * b(q, "jumlah")
        H.volume(M, nama, vol, "m3")
        H.material(M, "BETON", nama, vol, "m3")
        H.material(M, kode_besi, nama, vol, "m3")
    if P["lantai"] == 2:
        t = a["tangga"]
        pelat = n(t, "panjang_miring") * n(t, "lebar_tangga") * n(t, "tebal_pelat")
        anak = b(t, "jumlah_anak") * 0.5 * n(t, "tinggi_anak") * n(t, "lebar_anak") * n(t, "lebar_tangga")
        H.volume(M, "Tangga beton", pelat + anak, "m3")
        H.material(M, "BETON", "Tangga beton", pelat + anak, "m3")
        H.material(M, "BESI_TANGGA", "Tangga beton", pelat + anak, "m3")

def _bukaan(q, nama):
    """Luas bukaan = lebar x tinggi x jumlah (dilewati bila jumlah 0)."""
    jml = b(q, "jumlah", boleh_nol=True)
    if jml == 0:
        return 0.0
    return n(q, "lebar") * n(q, "tinggi") * jml

def modul4(P, A, H):
    """Dinding lantai 1 dan lantai 2 dihitung terpisah."""
    M = 4
    kode = "DINDING_BATA_MERAH" if P["dinding"] == "bata_merah" else "DINDING_BATA_RINGAN"
    total = 0.0
    for i in range(1, P["lantai"] + 1):
        q = A["m4"][f"lantai{i}"]
        bruto = n(q, "panjang_dinding") * n(q, "tinggi_dinding")
        buk = _bukaan(q["pintu"], "pintu") + _bukaan(q["jendela"], "jendela")
        if buk > bruto:
            raise InputError(f"Error: luas bukaan lantai {i} ({buk:.2f} m2) melebihi "
                             f"luas dinding ({bruto:.2f} m2).")
        bersih = bruto - buk
        if bersih <= 0:
            raise InputError(f"Error: luas dinding bersih lantai {i} harus lebih besar dari 0.")
        H.volume(M, f"Dinding bruto lantai {i}", bruto, "m2")
        H.volume(M, f"Bukaan pintu + jendela lantai {i}", buk, "m2")
        H.volume(M, f"Dinding bersih lantai {i}", bersih, "m2")
        H.material(M, kode, f"Dinding lantai {i}", bersih, "m2")
        total += bersih
    H.info["luas_dinding_bersih"] = total

# %% Cell 6: Rumus modul 5 sampai 8, mesin hitung, dan rekap
def modul5(P, A, H):
    a, M = A["m5"], 5
    pk, lk, label = ukuran_keramik(P)
    luas = 0.0
    for i in range(1, P["lantai"] + 1):
        l = n(a, f"luas_lantai{i}")
        H.volume(M, f"Luas lantai {i}", l, "m2")
        luas += l
    H.volume(M, "Luas keramik total", luas, "m2")
    # jumlah keping per m2 = 1 / (p x l)  -> waste ditambahkan di Hasil
    H.langsung(M, "Keramik lantai", luas, "m2", "Keramik lantai", f"{label} cm", "keping", 1 / (pk * lk))
    H.material(M, "KERAMIK_SPESI", "Spesi pemasangan keramik", luas, "m2")
    H.material(M, "KERAMIK_NAT", "Nat keramik", luas, "m2")

def modul6(P, A, H):
    """Luas bidang atap = luas proyeksi (termasuk overstek) / cos(kemiringan)."""
    a, M = A["m6"], 6
    jenis = pilihan(a.get("jenis_atap"), "jenis atap", ["pelana", "perisai"])
    alfa = n(a, "kemiringan_derajat")
    if alfa >= 85:
        raise InputError("Error: kemiringan atap harus lebih kecil dari 85 derajat.")
    o = n(a, "overstek", boleh_nol=True)
    Pp, Lp = P["panjang"] + 2 * o, P["lebar"] + 2 * o
    luas = Pp * Lp / math.cos(math.radians(alfa))
    naik = (Lp / 2) * math.tan(math.radians(alfa))
    if jenis == "pelana":
        nok = Pp
    else:
        if Pp < Lp:
            raise InputError("Error: atap perisai mengharuskan panjang bangunan >= lebar.")
        jurai = math.sqrt(2 * (Lp / 2) ** 2 + naik ** 2)
        nok = (Pp - Lp) + 4 * jurai
    H.volume(M, "Luas horizontal atap (dengan overstek)", Pp * Lp, "m2")
    H.volume(M, "Luas bidang atap (miring)", luas, "m2")
    H.volume(M, "Panjang nok + jurai", nok, "m")
    baja = P["rangka_atap"] == "baja_ringan"
    H.material(M, "ATAP_RANGKA_BAJA" if baja else "ATAP_RANGKA_KAYU", "Rangka atap", luas, "m2")
    H.material(M, "ATAP_AKSESORIS_BAJA" if baja else "ATAP_AKSESORIS_KAYU", "Sekrup / paku rangka", luas, "m2")
    gt = P["penutup_atap"] == "genteng_keramik"
    H.material(M, "PENUTUP_GENTENG_KERAMIK" if gt else "PENUTUP_SPANDEK", "Penutup atap", luas, "m2")
    H.material(M, "NOK_GENTENG_KERAMIK" if gt else "NOK_SPANDEK", "Nok atap", nok, "m")

def modul7(P, A, H, luas_dinding_bersih):
    a, M = A["m7"], 7
    sisi = b(a, "sisi_plester")
    if sisi not in (1, 2):
        raise InputError("Error: sisi plester harus 1 atau 2.")
    luas_p = luas_dinding_bersih * sisi
    H.volume(M, "Luas plesteran + acian + cat dinding", luas_p, "m2")
    H.material(M, "PLESTER", "Plesteran dinding", luas_p, "m2")
    H.material(M, "ACIAN", "Acian dinding", luas_p, "m2")
    H.material(M, "CAT_DINDING", "Cat dinding", luas_p, "m2")
    plafon = n(a, "luas_plafon")
    H.volume(M, "Luas plafon", plafon, "m2")
    H.material(M, "GYPSUM", "Plafon gypsum", plafon, "m2")
    H.material(M, "CAT_PLAFON", "Cat plafon", plafon, "m2")
    for kunci, kode, nama in (("pintu", "UNIT_PINTU", "Pintu"), ("jendela", "UNIT_JENDELA", "Jendela")):
        jml = b(a["unit"][kunci], "jumlah", boleh_nol=True)
        if jml:
            H.volume(M, f"Jumlah {nama.lower()}", jml, "unit")
            H.material(M, kode, nama, jml, "unit")

ITEM8 = [("pipa_air_bersih", "PIPA_AIR_BERSIH", "Pipa air bersih", "m"),
         ("pipa_air_kotor", "PIPA_AIR_KOTOR", "Pipa air kotor", "m"),
         ("kabel_listrik", "KABEL_LISTRIK", "Kabel listrik", "m"),
         ("titik_lampu", "TITIK_LAMPU", "Titik lampu", "unit"),
         ("stop_kontak", "STOP_KONTAK", "Stopkontak", "unit"),
         ("closet", "CLOSET", "Closet", "unit"),
         ("wastafel", "WASTAFEL", "Wastafel", "unit"),
         ("kran", "KRAN", "Kran air", "unit")]

def modul8(P, A, H):
    a, M = A["m8"], 8
    for kunci, kode, nama, sat in ITEM8:
        jml = b(a, kunci, True) if sat == "unit" else n(a, kunci, True)
        if jml > 0:
            H.volume(M, nama, jml, sat)
            H.material(M, kode, nama, jml, sat)

# --- default input (turunan dari identitas proyek, semua boleh diedit) ---
def default_input(P):
    k = round(2 * (P["panjang"] + P["lebar"]), 2)
    lt = P["lantai"]
    A = {
      "m1": {"panjang_galian": k, "lebar_galian": 0.6, "kedalaman_galian": 0.8,
             "tebal_urug_pasir": 0.1, "tebal_lantai_kerja": 0.05},
      "m2": ({"batu_kali": {"panjang_total": k, "lebar_atas": 0.3, "lebar_bawah": 0.6, "tinggi": 0.7}}
             if P["pondasi"] == "batu_kali" else
             {"footplat": {"jumlah_titik": 8, "sisi_x": 1.0, "sisi_y": 1.0, "tebal": 0.3}}),
      "m3": {"elemen": {
                "sloof":  {"panjang": k, "lebar": 0.15, "tinggi": 0.20, "jumlah": 1},
                "kolom1": {"panjang": 0.15, "lebar": 0.15, "tinggi": P["tinggi1"], "jumlah": 10},
                "balok1": {"panjang": k, "lebar": 0.15, "tinggi": 0.25, "jumlah": 1}}},
      "m4": {}, "m5": {}, "m7": {}, 
      "m6": {"jenis_atap": "pelana", "kemiringan_derajat": 30, "overstek": 0.6},
      "m8": {"pipa_air_bersih": 40, "pipa_air_kotor": 30, "kabel_listrik": 200,
             "titik_lampu": 15, "stop_kontak": 12, "closet": 2, "wastafel": 2, "kran": 4},
    }
    if lt == 2:
        A["m3"]["elemen"]["kolom2"] = {"panjang": 0.15, "lebar": 0.15, "tinggi": P["tinggi2"], "jumlah": 10}
        A["m3"]["elemen"]["balok2"] = {"panjang": k, "lebar": 0.15, "tinggi": 0.25, "jumlah": 1}
        A["m3"]["elemen"]["pelat"] = {"panjang": P["panjang"], "lebar": P["lebar"], "tinggi": 0.12, "jumlah": 1}
        A["m3"]["tangga"] = {"panjang_miring": 4.0, "lebar_tangga": 1.0, "tebal_pelat": 0.12,
                             "jumlah_anak": 18, "tinggi_anak": 0.18, "lebar_anak": 0.27}
    for i in range(1, lt + 1):
        A["m4"][f"lantai{i}"] = {"panjang_dinding": k, "tinggi_dinding": P["tinggi1"] if i == 1 else P["tinggi2"],
                                 "pintu": {"lebar": 0.9, "tinggi": 2.1, "jumlah": 3},
                                 "jendela": {"lebar": 1.0, "tinggi": 1.2, "jumlah": 4}}
        A["m5"][f"luas_lantai{i}"] = round(P["panjang"] * P["lebar"], 2)
    A["m7"] = {"sisi_plester": 2, "luas_plafon": round(P["panjang"] * P["lebar"] * lt, 2),
               "unit": {"pintu": {"jumlah": 3 * lt}, "jendela": {"jumlah": 4 * lt}}}
    return A

# --- mesin hitung ---
URUTAN = [2, 3, 4, 5, 6, 1, 7, 8]      # modul 1 butuh hasil modul 2; modul 7 butuh modul 4
DEPEND = {1: {2}, 7: {4}}

def hitung(P, A, daftar=None):
    """Hitung semua modul (atau hanya yang ada di 'daftar'). Mengembalikan Hasil."""
    P = validasi_proyek(P)
    mau = set(daftar) if daftar else set(range(1, 9))
    perlu = set(mau)
    for m in mau:
        perlu |= DEPEND.get(m, set())
    H = Hasil()
    for m in URUTAN:
        if m not in perlu:
            continue
        if m == 1:   modul1(P, A, H, H.info["vol_pondasi"])
        elif m == 7: modul7(P, A, H, H.info["luas_dinding_bersih"])
        else:        globals()[f"modul{m}"](P, A, H)
    H.vol = sorted([r for r in H.vol if r["no"] in mau], key=lambda r: r["no"])
    H.mat = sorted([r for r in H.mat if r["no"] in mau], key=lambda r: r["no"])
    H.P = P
    return H

# --- rekapitulasi ---
def tabel_volume(H):
    return pd.DataFrame(H.vol, columns=["modul", "uraian", "jumlah", "satuan"])

def tabel_detail(H):
    return pd.DataFrame(H.mat, columns=["modul", "uraian", "material", "spesifikasi",
                                        "volume", "satuan_volume", "koefisien", "waste",
                                        "kebutuhan", "satuan"])

def rekap_pekerjaan(H):
    """Rekap A: kebutuhan material per kelompok pekerjaan."""
    d = pd.DataFrame(H.mat)
    if d.empty:
        return d
    return (d.groupby(["no", "modul", "material", "spesifikasi", "satuan"], as_index=False)
              ["kebutuhan"].sum().drop(columns="no"))

def harga_terpilih():
    h = HARGA.copy()
    if MODE_HARGA == "min":   h["harga"] = h["harga_min"]
    elif MODE_HARGA == "max": h["harga"] = h["harga_max"]
    else:                     h["harga"] = (h["harga_min"] + h["harga_max"]) / 2
    return h[["material", "spesifikasi", "satuan", "harga"]]

def rekap_material(H):
    """Rekap B: total per (material + spesifikasi + satuan). Spesifikasi berbeda TIDAK digabung."""
    d = pd.DataFrame(H.mat)
    if d.empty:
        return d
    r = d.groupby(["material", "spesifikasi", "satuan"], as_index=False).agg(
        kebutuhan=("kebutuhan", "sum"), waste=("waste", "first"),
        asal=("no", lambda s: ", ".join(NAMA_MODUL[i] for i in sorted(set(s)))))
    r["kebutuhan_pesan"] = [math.ceil(round(x, 6)) if s in DISKRIT else x
                            for x, s in zip(r["kebutuhan"], r["satuan"])]
    r = r.merge(harga_terpilih(), on=["material", "spesifikasi", "satuan"], how="left")
    r["biaya"] = r["kebutuhan_pesan"] * r["harga"]
    return r

def periksa_ganda(H):
    """Pemeriksaan perhitungan ganda: baris yang identik tidak boleh muncul dua kali."""
    d = pd.DataFrame(H.mat)
    return d[d.duplicated(["no", "uraian", "material", "spesifikasi"], keep=False)]

# %% Cell 7: Ekspor ke Excel
def ratakan(d, awal=""):
    """Ubah dict bertingkat menjadi daftar (nama, nilai) untuk sheet Data Input."""
    out = []
    for k, v in d.items():
        nama = f"{awal} > {k}" if awal else k
        out += ratakan(v, nama) if isinstance(v, dict) else [(nama, v)]
    return out

def ekspor_excel(P, A, H, path="Estimasi_Material.xlsx"):
    """Tulis 5 sheet utama (+ Waste dan Harga) lalu kembalikan path file."""
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        pd.DataFrame(list(P.items()), columns=["Data", "Nilai"]).to_excel(xw, sheet_name="Identitas Proyek", index=False)
        pd.DataFrame(ratakan(A), columns=["Input", "Nilai"]).to_excel(xw, sheet_name="Data Input", index=False)
        tabel_volume(H).to_excel(xw, sheet_name="Rekap Pekerjaan", index=False)
        tabel_detail(H).to_excel(xw, sheet_name="Rekap Pekerjaan", index=False, startrow=len(H.vol) + 3)
        rekap_material(H).to_excel(xw, sheet_name="Rekap Material", index=False)
        DB.to_excel(xw, sheet_name="Database Koefisien", index=False)
        pd.DataFrame(list(WASTE.items()), columns=["Material", "Waste"]).to_excel(xw, sheet_name="Waste", index=False)
        HARGA.to_excel(xw, sheet_name="Harga Bahan", index=False)
        for ws in xw.book.worksheets:                      # lebar kolom otomatis
            for kol in ws.columns:
                lebar = max(len(str(c.value)) if c.value is not None else 0 for c in kol)
                ws.column_dimensions[kol[0].column_letter].width = min(lebar + 2, 45)
    return path
