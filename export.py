import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

def buat_pdf(P, H, rekap):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), rightMargin=28, leftMargin=28, topMargin=28, bottomMargin=28)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("LAPORAN ESTIMASI KEBUTUHAN MATERIAL", styles["Title"]),
        Spacer(1, 8),
        Paragraph(f"Proyek: {P.get('nama','-')} | Pemilik: {P.get('pemilik','-')}", styles["Normal"]),
        Paragraph(f"Dimensi: {P.get('panjang')} m x {P.get('lebar')} m | Jumlah lantai: {P.get('lantai')}", styles["Normal"]),
        Spacer(1, 14),
        Paragraph("Rekap Volume Pekerjaan", styles["Heading2"])
    ]
    volume = [["Modul", "Uraian", "Jumlah", "Satuan"]]
    for r in H.vol:
        volume.append([r["modul"], r["uraian"], f'{r["jumlah"]:,.3f}', r["satuan"]])
    t=Table(volume, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#17324D")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),.35,colors.grey),
        ("FONTSIZE",(0,0),(-1,-1),7),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F1F5F8")])
    ]))
    story += [t, Spacer(1,14), Paragraph("Rekap Kebutuhan Material dan Biaya", styles["Heading2"])]
    data=[["Material","Spesifikasi","Kebutuhan pesan","Satuan","Harga","Biaya"]]
    for _,r in rekap.iterrows():
        harga = "-" if r.get("harga") is None or str(r.get("harga"))=="nan" else f'{r["harga"]:,.0f}'
        biaya = "-" if r.get("biaya") is None or str(r.get("biaya"))=="nan" else f'{r["biaya"]:,.0f}'
        data.append([str(r["material"]),str(r["spesifikasi"]),f'{r["kebutuhan_pesan"]:,.3f}',str(r["satuan"]),harga,biaya])
    tt=Table(data, repeatRows=1)
    tt.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#17324D")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),.35,colors.grey),
        ("FONTSIZE",(0,0),(-1,-1),7),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F1F5F8")])
    ]))
    story.append(tt)
    story.append(Spacer(1,10))
    story.append(Paragraph("Catatan: hasil merupakan estimasi awal. Verifikasi koefisien, harga, gambar kerja, dan kondisi lapangan sebelum digunakan sebagai dasar pelaksanaan.",styles["Italic"]))
    doc.build(story)
    return buf.getvalue()
