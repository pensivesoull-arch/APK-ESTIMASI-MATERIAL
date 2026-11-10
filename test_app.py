import core
P=core.validasi_proyek({"nama":"Uji","pemilik":"-","lantai":2,"panjang":10,"lebar":8,"tinggi1":3.5,"tinggi2":3.5,"pondasi":"batu_kali","dinding":"bata_merah","rangka_atap":"baja_ringan","penutup_atap":"genteng_keramik","keramik":"40x40"})
A=core.default_input(P)
H=core.hitung(P,A)
assert len(H.vol)>0 and len(H.mat)>0
assert core.periksa_ganda(H).empty
print("LULUS: mesin perhitungan menghasilkan",len(H.vol),"item pekerjaan dan",len(H.mat),"baris material.")
