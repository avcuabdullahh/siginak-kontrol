import flet as ft
import math
import os
from fpdf import FPDF

# --- TÜRKÇE KARAKTER DÜZELTME ---
def tr_to_eng(text):
    if not isinstance(text, str): text = str(text)
    replacements = {'ı':'i', 'İ':'I', 'ğ':'g', 'Ğ':'G', 'ü':'u', 'Ü':'U', 
                    'ş':'s', 'Ş':'S', 'ö':'o', 'Ö':'O', 'ç':'c', 'Ç':'C'}
    for tr, eng in replacements.items(): text = text.replace(tr, eng)
    return text

def main(page: ft.Page):
    page.title = "Sığınak Kontrol"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20
    page.window_width = 400

    data = {}

    # --- YARDIMCI FONKSİYONLAR ---
    def create_textfield(label, is_number=False, default=""):
        return ft.TextField(label=label, value=default, keyboard_type=ft.KeyboardType.NUMBER if is_number else ft.KeyboardType.TEXT, width=page.window_width)

    def create_dropdown(label, options):
        return ft.Dropdown(label=label, options=[ft.dropdown.Option(opt) for opt in options], value=options[0] if options else None)

    # --- ARAYÜZ KONTEYNERLERİ ---
    login_view = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    wizard_view = ft.Column(visible=False, spacing=20)
    
    # --- ADIM 1: PROJE BİLGİLERİ ---
    adim1_col = ft.Column(visible=True)
    inputs_adim1 = {
        "yapi_sahibi": create_textfield("Yapı Sahibi / Yapı Sınıfı:"),
        "muellif": create_textfield("Proje Müellifi (Çizen):"),
        "kontrol_personeli": create_textfield("Proje Kontrol Personeli:"),
        "tarih": create_textfield("Proje/Kontrol Tarihi:"),
        "adres": create_textfield("Yapı Adresi:"),
        "ada_parsel": create_textfield("Ada / Parsel No:"),
        "ruhsat": create_textfield("Ruhsat / İskan No:")
    }
    adim1_col.controls.extend([ft.Text("Adım 1: Proje Bilgileri", size=20, weight="bold")] + list(inputs_adim1.values()))

    # --- ADIM 2: ZORUNLULUK ---
    adim2_col = ft.Column(visible=False)
    zorunluluk_radio = ft.RadioGroup(
        content=ft.Column([
            ft.Radio(value="1", label="[1] 10+ bağımsız bölüm konut"),
            ft.Radio(value="2", label="[2] 1500 m² üstü konut dışı / 1000 m² resmi"),
            ft.Radio(value="3", label="[3] Karma kullanım (Konut 10+ veya 1500 m²)"),
            ft.Radio(value="4", label="[4] Yatak 50+ veya 25+ (sağlık)"),
            ft.Radio(value="5", label="[5] 2000 m² üstü sanayi"),
            ft.Radio(value="6", label="[6] 5000+ kapasiteli stadyum"),
            ft.Radio(value="0", label="[0] Şartları sağlamıyor"),
            ft.Radio(value="42", label="[42] Admin Onay")
        ]),
        value="0"
    )
    adim2_col.controls.extend([ft.Text("Adım 2: Sığınak Zorunluluğu", size=20, weight="bold"), zorunluluk_radio])

    # --- ADIM 3: ALAN VE KİŞİ ---
    adim3_col = ft.Column(visible=False)
    kategori_dd = create_dropdown("Yapı Türü Seçiniz", ["1- Konut", "2- Konaklama", "3- Diğer/Ofis", "4- Stadyum", "5- Sanayi"])
    
    # Dinamik Alanlar
    oda1 = create_textfield("1 Odalı B.Bölüm:", True, "0"); oda2 = create_textfield("2 Odalı B.Bölüm:", True, "0"); oda3 = create_textfield("3+ Odalı B.Bölüm:", True, "0")
    yatak = create_textfield("Toplam Yatak:", True, "0")
    emsal = create_textfield("Emsal Alanı (m²):", True, "0")
    seyirci = create_textfield("Seyirci Kapasitesi:", True, "0")
    personel = create_textfield("Personel Sayısı:", True, "0")
    
    dinamik_kutu = ft.Column()
    hesap_lbl = ft.Text(">>> Hesaplamalar burada görünecek...", color=ft.colors.BLUE, weight="bold")
    
    p_alan = create_textfield("Projede Ayrılan Net Alan (m²):", True)
    p_erkek = create_textfield("Erkek WC Sayısı:", True); p_kadin = create_textfield("Kadın WC Sayısı:", True)
    klozet = create_dropdown("Klozet var mı?", ["Evet", "Hayır"])
    kanal = create_dropdown("Kanalizasyona bağlı mı?", ["Evet", "Hayır"])
    ventil = create_dropdown("Geri tepme ventili var mı?", ["Evet", "Hayır"])
    
    mutfak_kutu = ft.Column(visible=False)
    mutfak_var = create_dropdown("Mutfak nişi var mı?", ["Evet", "Hayır"])
    mutfak_alan = create_textfield("Mutfak Nişi Alanı (m²):", True, "0")
    mutfak_kutu.controls.extend([ft.Text("Mutfak Nişi (100m² üstü)"), mutfak_var, mutfak_alan])
    
    ekipman = create_dropdown("Yangın söndürme/İlkyardım var mı?", ["Evet", "Hayır"])
    atik = create_dropdown("Çöp atık uzaklaştırma uygun mu?", ["Evet", "Hayır"])
    detay = create_dropdown("Projelerde detay var mı?", ["Evet", "Hayır"])
    yukseklik = create_textfield("Sığınağın Net İç Yüksekliği (m):", True, "2.40")

    def adim3_hesapla(e=None):
        idx = ["1- Konut", "2- Konaklama", "3- Diğer/Ofis", "4- Stadyum", "5- Sanayi"].index(kategori_dd.value)
        kisi = 0.0
        try:
            if idx == 0: kisi = (float(oda1.value or 0)*2) + (float(oda2.value or 0)*3) + (float(oda3.value or 0)*4)
            elif idx == 1: kisi = float(yatak.value or 0) * 1.2
            elif idx == 2: kisi = float(emsal.value or 0) / 20.0
            elif idx == 3: kisi = float(seyirci.value or 0) * 0.03
            elif idx == 4: kisi = float(personel.value or 0)
        except: pass

        kisi = math.ceil(kisi)
        min_alan = kisi * 1.0
        if idx == 4 and min_alan < 20.0: min_alan = 20.0

        t_wc = kisi // 100
        ilave = 1 if (kisi % 100) > 50 else 0
        req_wc = max(1, t_wc + ilave)

        hesap_lbl.value = f"📐 Kişi: {kisi} | Min Alan: {min_alan} m² | Gerekli WC: {req_wc} E, {req_wc} K"
        mutfak_kutu.visible = min_alan > 100
        data.update({"kisi": kisi, "min_alan": min_alan, "req_wc": req_wc, "sistem_toplam_wc": req_wc * 2})
        page.update()

    def adim3_arayuz_guncelle(e):
        dinamik_kutu.controls.clear()
        idx = ["1- Konut", "2- Konaklama", "3- Diğer/Ofis", "4- Stadyum", "5- Sanayi"].index(kategori_dd.value)
        if idx == 0: dinamik_kutu.controls.extend([oda1, oda2, oda3])
        elif idx == 1: dinamik_kutu.controls.append(yatak)
        elif idx == 2: dinamik_kutu.controls.append(emsal)
        elif idx == 3: dinamik_kutu.controls.append(seyirci)
        elif idx == 4: dinamik_kutu.controls.append(personel)
        adim3_hesapla()
        page.update()

    kategori_dd.on_change = adim3_arayuz_guncelle
    for inp in [oda1, oda2, oda3, yatak, emsal, seyirci, personel]: inp.on_change = adim3_hesapla
    
    adim3_col.controls.extend([ft.Text("Adım 3: Alan ve Tesisat", size=20, weight="bold"), kategori_dd, dinamik_kutu, hesap_lbl, p_alan, ft.Row([p_erkek, p_kadin]), klozet, kanal, ventil, mutfak_kutu, ekipman, atik, detay, yukseklik])

    # --- ADIM 4: HAVALANDIRMA ---
    adim4_col = ft.Column(visible=False)
    lbl_kapi = ft.Text("Kapı Hesabı...", color=ft.colors.BLUE)
    p_kapi = create_textfield("Projedeki Kapı Sayısı:", True)
    kapi_nitelik = create_dropdown("Kapılar demir/dik açılı mı?", ["Evet", "Hayır"])
    
    lbl_debi = ft.Text("Taze Hava Debisi...", color=ft.colors.BLUE)
    p_debi = create_textfield("Projedeki Havalandırma Debisi (m³/h):", True)

    wc_var = create_dropdown("Tuvalet egzozu var mı?", ["Evet", "Hayır"])
    wc_tip = create_dropdown("Çalışma Tipi:", ["Kullanım Anında (8 ACH)", "Sürekli (5 ACH)"])
    wc_alan = create_textfield("Bir WC Alanı (m²):", True, "0"); wc_h = create_textfield("WC Yüksekliği (m):", True, "0")
    lbl_wc_debi = ft.Text("Gerekli Egzoz...", color=ft.colors.BLUE)
    p_wc_debi = create_textfield("Projedeki Egzoz Debisi:", True, "0")
    
    duman_kutu = ft.Column(visible=False)
    duman_var = create_dropdown("Duman tahliye sistemi var mı?", ["Evet", "Hayır"])
    lbl_duman_debi = ft.Text("Gerekli Duman Debisi...", color=ft.colors.BLUE)
    p_duman_debi = create_textfield("Projedeki Duman Debisi:", True, "0")
    duman_kutu.controls.extend([duman_var, lbl_duman_debi, p_duman_debi])

    f_sinif = create_dropdown("Tehlike Sınıfı:", ["Yüksek", "Düşük/Orta"])
    f_kum = create_dropdown("Kum Filtresi?", ["Evet", "Hayır"])
    f_g4 = create_dropdown("G4 Filtre?", ["Evet", "Hayır"])
    f_aktif = create_dropdown("Aktif Karbon?", ["Evet", "Hayır"])
    f_radyo = create_dropdown("Radyoaktif Filtre?", ["Evet", "Hayır"])

    def adim4_hazirla():
        alan = data.get("min_alan", 0); kisi = data.get("kisi", 0)
        req_kapi = 2 if alan > 100 else 1
        data["req_kapi"] = req_kapi
        lbl_kapi.value = f"🚪 Asgari {req_kapi} çıkış kapısı gerekli."
        
        k_basi = 1.8 if kisi <= 50 else (3.0 if kisi <= 150 else 4.5)
        data["req_hava"] = kisi * k_basi
        lbl_debi.value = f"💨 Gerekli Taze Hava: {data['req_hava']:.2f} m³/h"

        if alan > 100:
            duman_kutu.visible = True
            h = float(yukseklik.value or 2.40)
            data["req_duman"] = float(p_alan.value or 0) * h * 10
            lbl_duman_debi.value = f"🔥 Gerekli Duman: {data['req_duman']:.2f} m³/h"
        else:
            duman_kutu.visible = False; data["req_duman"] = 0
            
    def adim4_hesapla(e=None):
        try:
            ach = 8.0 if wc_tip.value.startswith("Kul") else 5.0
            a = float(wc_alan.value or 0); h = float(wc_h.value or 0)
            tot_wc = data.get("sistem_toplam_wc", 2)
            data["req_egzoz"] = a * h * ach * tot_wc
            lbl_wc_debi.value = f"🚽 Gerekli Egzoz: {data['req_egzoz']:.2f} m³/h"
        except: pass
        page.update()

    for inp in [wc_alan, wc_h, wc_tip]: inp.on_change = adim4_hesapla

    adim4_col.controls.extend([ft.Text("Adım 4: Havalandırma", size=20, weight="bold"), lbl_kapi, p_kapi, kapi_nitelik, lbl_debi, p_debi, ft.Text("WC Egzoz", weight="bold"), wc_var, wc_tip, wc_alan, wc_h, lbl_wc_debi, p_wc_debi, duman_kutu, ft.Text("Filtreler", weight="bold"), f_sinif, f_kum, f_g4, f_aktif, f_radyo])

    # --- ADIM 5: DONANIM VE ONAY ---
    adim5_col = ft.Column(visible=False)
    cb_guc = create_dropdown("Fan motoruna uygun jeneratör/UPS var mı?", ["Evet", "Hayır"])
    cb_tip = create_dropdown("↳ Mevcut güç kaynağı nedir?", ["Jeneratör", "UPS"])
    cb_jdis = create_dropdown("↳ Jeneratör sığınak alanı DIŞINDA mı?", ["Evet", "Hayır"])
    cb_jegz = create_dropdown("↳ Jeneratör egzozu DIŞARIYA verilmiş mi?", ["Evet", "Hayır"])
    cb_kol = create_dropdown("Fana bağlı çevirmeli kol mevcut mu?", ["Evet", "Hayır"])
    cb_iletisim = create_dropdown("İletişim prizi/Wi-Fi mevcut mu?", ["Evet", "Hayır"])
    cb_ozel = create_dropdown("Yapı resmi/sağlık/eğitim binası mı?", ["Hayır", "Evet"])
    cb_elek = create_dropdown("↳ En az 24 saat kesintisiz elektrik var mı?", ["Evet", "Hayır"])

    def adim5_arayuz_guncelle(e=None):
        jen = cb_tip.value == "Jeneratör" and cb_guc.value == "Evet"
        cb_tip.visible = cb_guc.value == "Evet"
        cb_jdis.visible = jen; cb_jegz.visible = jen
        cb_elek.visible = cb_ozel.value == "Evet"
        page.update()
        
    cb_guc.on_change = adim5_arayuz_guncelle; cb_tip.on_change = adim5_arayuz_guncelle; cb_ozel.on_change = adim5_arayuz_guncelle
    adim5_col.controls.extend([ft.Text("Adım 5: Donanım", size=20, weight="bold"), cb_guc, cb_tip, cb_jdis, cb_jegz, cb_kol, cb_iletisim, cb_ozel, cb_elek])

    # --- SİHİRBAZ YÖNETİMİ ---
    adimlar = [adim1_col, adim2_col, adim3_col, adim4_col, adim5_col]
    aktif_adim = 0

    def rapor_olustur_ve_kaydet():
        # Validasyon ve Eksik Tespiti (Özetlenmiş)
        eksik3 = []; eksik4 = []; eksik5 = []
        try:
            if float(p_alan.value) < data["min_alan"]: eksik3.append("Alan yetersiz")
            if float(p_erkek.value) < data["req_wc"] or float(p_kadin.value) < data["req_wc"]: eksik3.append("WC yetersiz")
            if klozet.value == "Hayır": eksik3.append("Hela taşı kullanılmış")
            data["adim3_durum"] = "UYGUN" if not eksik3 else "UYGUN DEĞİLDİR"
            data["adim3_eksikler"] = " \n- ".join(eksik3)
            
            if float(p_kapi.value) < data["req_kapi"]: eksik4.append("Kapı yetersiz")
            if float(p_debi.value) < data["req_hava"]: eksik4.append("Taze hava yetersiz")
            data["adim4_durum"] = "UYGUN" if not eksik4 else "UYGUN DEĞİLDİR"
            data["adim4_eksikler"] = " \n- ".join(eksik4)
            
            if cb_guc.value == "Hayır": eksik5.append("Jeneratör/UPS yok")
            if cb_kol.value == "Hayır": eksik5.append("Çevirmeli kol eksik")
            data["adim5_durum"] = "UYGUN" if not eksik5 else "UYGUN DEĞİLDİR"
            data["adim5_eksikler"] = " \n- ".join(eksik5)
        except:
            page.snack_bar = ft.SnackBar(ft.Text("Lütfen alanları doğru formatta doldurun!")); page.snack_bar.open = True; page.update(); return

        # PDF OLUŞTURMA (Android'e Uygun Path ile)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Times", 'B', 16)
        pdf.cell(0, 10, txt=tr_to_eng("SIGINAK GENEL DENETIM RAPORU"), ln=True, align='C')
        pdf.ln(5)
        
        pdf.set_font("Times", 'B', 12)
        pdf.cell(190, 8, txt=tr_to_eng("1. PROJE VE KONTROL BILGILERI"), border=1, ln=True, align='C')
        pdf.set_font("Times", '', 11)
        pdf.cell(50, 8, txt="Ruhsat No:", border=1); pdf.cell(140, 8, txt=tr_to_eng(inputs_adim1['ruhsat'].value), border=1, ln=True)
        pdf.cell(50, 8, txt="Kontrol Personeli:", border=1); pdf.cell(140, 8, txt=tr_to_eng(inputs_adim1['kontrol_personeli'].value), border=1, ln=True)
        
        # Sonuç Yazdırma
        a3 = data['adim3_durum'] == "UYGUN"; a4 = data['adim4_durum'] == "UYGUN"; a5 = data['adim5_durum'] == "UYGUN"
        genel = "ONAY" if (a3 and a4 and a5) else "RED"
        pdf.ln(5); pdf.set_font("Times", 'B', 12)
        pdf.cell(190, 10, txt=tr_to_eng(f"RAPOR GENEL DURUMU: {genel}"), border=1, ln=True, align='C')

        # ANDROID KAYIT YOLU (Download Klasörü veya Uygulama Dizini)
        android_download = os.environ.get('EXTERNAL_STORAGE', '/storage/emulated/0/Download')
        if not os.path.exists(android_download): android_download = page.client_storage.path # Fallback
        
        ruhsat_no = tr_to_eng(inputs_adim1['ruhsat'].value or "Rapor").replace('/', '_')
        dosya_yolu = os.path.join(android_download, f"{ruhsat_no}_Siginak.pdf")
        
        try:
            pdf.output(dosya_yolu)
            page.snack_bar = ft.SnackBar(ft.Text(f"Rapor Başarıyla Kaydedildi: {dosya_yolu}"), bgcolor=ft.colors.GREEN)
        except Exception as e:
            page.snack_bar = ft.SnackBar(ft.Text(f"PDF Hatası: {e}"), bgcolor=ft.colors.RED)
        page.snack_bar.open = True
        page.update()

    def ileri_git(e):
        nonlocal aktif_adim
        if aktif_adim == 1 and zorunluluk_radio.value == "0":
            page.snack_bar = ft.SnackBar(ft.Text("Sığınak zorunlu değil. İşlem sonlandırıldı.")); page.snack_bar.open = True; page.update(); return
            
        if aktif_adim < len(adimlar) - 1:
            if aktif_adim == 2: adim4_hazirla(); adim4_hesapla() # Adım 4'e geçerken değerleri taşı
            adimlar[aktif_adim].visible = False
            aktif_adim += 1
            adimlar[aktif_adim].visible = True
            btn_ileri.text = "Rapor Oluştur" if aktif_adim == len(adimlar) - 1 else "İleri >"
            btn_geri.visible = True
        else:
            rapor_olustur_ve_kaydet()
        page.update()

    def geri_git(e):
        nonlocal aktif_adim
        if aktif_adim > 0:
            adimlar[aktif_adim].visible = False
            aktif_adim -= 1
            adimlar[aktif_adim].visible = True
            btn_ileri.text = "İleri >"
            btn_geri.visible = aktif_adim > 0
        page.update()

    btn_ileri = ft.ElevatedButton("İleri >", on_click=ileri_git)
    btn_geri = ft.ElevatedButton("< Geri", on_click=geri_git, visible=False)
    btn_row = ft.Row([btn_geri, btn_ileri], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    wizard_view.controls.extend(adimlar + [ft.Divider(), btn_row])

    # --- ŞİFRE EKRANI MANTIĞI ---
    def login_kontrol(e):
        if sifre_input.value == "4242":
            login_view.visible = False
            wizard_view.visible = True
            adim3_arayuz_guncelle(None)
            adim5_arayuz_guncelle(None)
        else:
            sifre_input.error_text = "Hatalı şifre!"
        page.update()

    sifre_input = ft.TextField(label="Sığınak Kontrol Şifresi", password=True, text_align=ft.TextAlign.CENTER)
    btn_login = ft.ElevatedButton("Giriş Yap", on_click=login_kontrol)
    login_view.controls.extend([ft.Icon(ft.icons.SECURITY, size=50), sifre_input, btn_login])

    page.add(login_view, wizard_view)

ft.app(target=main)