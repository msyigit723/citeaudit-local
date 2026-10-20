"""
CiteAudit Local - Demo PDF Generator
Hacktoberfest 2026

Bu script, CiteAudit Local jüri demosu için Türkçe karakter uyumlu örnek
tez taslağını ve doğrulanabilir kaynak PDF'leri üretir.
"""

from pathlib import Path
import pymupdf


def create_demo_pdfs(output_dir: str = "sample_data") -> dict[str, str]:
    """Demo için Türkçe karakter uyumlu örnek tez ve kaynak PDF'lerini üretir."""
    target_path = Path(output_dir)
    target_path.mkdir(parents=True, exist_ok=True)

    created_files = {}

    # Ortak CSS stili (Temiz tipografi ve Türkçe karakter desteği)
    base_css = """
    <style>
        body {
            font-family: sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #1a202c;
            margin: 0;
            padding: 0;
        }
        h1 {
            font-size: 16pt;
            font-weight: bold;
            color: #0f172a;
            margin-bottom: 8px;
            text-align: center;
        }
        h2 {
            font-size: 13pt;
            font-weight: bold;
            color: #1e293b;
            margin-top: 18px;
            margin-bottom: 6px;
            border-bottom: 1px solid #cbd5e1;
            padding-bottom: 4px;
        }
        p {
            margin-bottom: 12px;
            text-align: justify;
        }
        .meta {
            text-align: center;
            font-size: 10pt;
            color: #475569;
            margin-bottom: 20px;
        }
        .ref-item {
            font-size: 9.5pt;
            margin-bottom: 8px;
            text-indent: -20px;
            padding-left: 20px;
        }
    </style>
    """

    # -------------------------------------------------------------
    # 1. Tez_Taslagi.pdf
    # -------------------------------------------------------------
    thesis_file = target_path / "Tez_Taslagi.pdf"
    doc_thesis = pymupdf.open()
    page1 = doc_thesis.new_page(width=595, height=842)  # A4

    thesis_html = f"""
    {base_css}
    <h1>Bölgesel Tarım ve Klinik Sistemlerde Yapay Zeka Uygulamaları</h1>
    <div class="meta">
        <strong>Doktora Tez Taslağı</strong> &bull; Bilgisayar Mühendisliği Enstitüsü &bull; 2026
    </div>

    <h2>1. Giriş ve Literatür Özeti</h2>
    <p>
        Günümüzde açık ağırlıklı büyük dil modelleri ve derin konvolüsyonel sinir ağları,
        bölgesel kalkınma odaklı projelerde ve sağlık enformatiğinde kritik rol oynamaktadır.
        Özellikle tarımsal verimlilik analizlerinde görüntü tabanlı modellerin doğruluğu
        büyük önem taşımaktadır.
    </p>
    <p>
        Derin öğrenme tabanlı görüntü işleme modelleri Elazığ yöresi kayısı yaprağı
        hastalıklarının tespitinde %94,2 doğruluk oranına ulaşmıştır [1].
    </p>
    <p>
        Öte yandan, sağlık bilişiminde hasta gizliliği ve işlem gecikmesi en büyük darboğazı
        oluşturmaktadır. Özel nitelikli sağlık verilerinin işlenmesinde yerel açık ağırlıklı dil
        modelleri bulut API sistemlerine göre %50 daha yavaş çalışmaktadır ve KVKK açısından
        klinik kullanıma uygun değildir [2].
    </p>
    <p>
        Aynı çalışmada kayısı çekirdeği yağının kozmetik sektöründeki ihracat gelirlerini
        üç katına çıkardığı kanıtlanmıştır [1].
    </p>
    <p>
        Son olarak meteorolojik kestirimlerde ve hidrolojik modellemelerde yeni nesil temsil yöntemleri
        denenmiştir. Kuantum tabanlı vektör veritabanları Fırat Havzası mikro-iklim tahminlerinde
        %99,9 kesinlik sağlamıştır [3].
    </p>

    <h2>KAYNAKÇA</h2>
    <div class="ref-item">
        [1] Kaya, A., & Demir, M. (2024). Derin Öğrenme ile Kayısı Yaprağı Hastalıklarının Sınıflandırılması. Fırat Mühendislik Dergisi.
    </div>
    <div class="ref-item">
        [2] Yılmaz, S., & Çelik, E. (2025). Klinik Metin Özetlemede Yerel Açık Ağırlıklı Modellerin KVKK ve Hız Performansı. Tıp Bilişimi Kongresi.
    </div>
    <div class="ref-item">
        [3] Thorne, R., & Vance, K. (2025). Quantum Hyper-Vector Databases in Anatolian Micro-Climate Forecasting. Journal of NonExistent AI Studies.
    </div>
    """

    page1.insert_htmlbox(pymupdf.Rect(50, 50, 545, 790), thesis_html)
    doc_thesis.save(str(thesis_file))
    doc_thesis.close()
    created_files["thesis"] = str(thesis_file)

    # -------------------------------------------------------------
    # 2. 1.pdf (Kaynak 1) - 2 Sayfa
    # -------------------------------------------------------------
    source1_file = target_path / "1.pdf"
    doc_s1 = pymupdf.open()

    # Sayfa 1
    s1_p1 = doc_s1.new_page(width=595, height=842)
    s1_p1_html = f"""
    {base_css}
    <h1>Derin Öğrenme ile Kayısı Yaprağı Hastalıklarının Sınıflandırılması</h1>
    <div class="meta">
        Ali Kaya, Mehmet Demir &bull; Fırat Mühendislik Dergisi &bull; Cilt 36, Sayı 2, 2024
    </div>
    <h2>Özet ve Çalışmanın Amacı</h2>
    <p>
        Doğu Anadolu Bölgesi, Türkiye'nin ve dünyanın en önemli kayısı üretim merkezlerinden biridir.
        Ağaç yapraklarında görülen fungal ve bakteriyel hastalıklar rekolte kaybına yol açmaktadır.
        Bu çalışmanın temel amacı, yaprak lezyonlarının yapay zeka yöntemleriyle saha koşullarında
        yüksek doğrulukla tespit edilmesidir.
    </p>
    <h2>Materyal ve Metot</h2>
    <p>
        Elazığ ve Malatya havzasından toplanan 12.000 yüksek çözünürlüklü yaprak fotoğrafı etiketlenmiş;
        veri artırma teknikleri uygulanarak eğitim ve test setleri oluşturulmuştur.
    </p>
    """
    s1_p1.insert_htmlbox(pymupdf.Rect(50, 50, 545, 790), s1_p1_html)

    # Sayfa 2
    s1_p2 = doc_s1.new_page(width=595, height=842)
    s1_p2_html = f"""
    {base_css}
    <h2>Deneysel Bulgular ve Sonuçlar</h2>
    <p>
        Deneysel sonuçlarımızda CNN ve Vision Transformer tabanlı derin öğrenme modelleri
        Elazığ yöresi kayısı yaprağı hastalıklarının tespitinde %94,2 doğruluk oranına ulaşmıştır.
        Çalışmamızda sadece yaprak görüntüleri incelenmiş olup kayısı çekirdeği yağı veya kozmetik
        ihracatı üzerine hiçbir veri veya analiz bulunmamaktadır.
    </p>
    <p>
        Gelecek çalışmalarda mobil cihazlarda çalışabilecek hafifletilmiş mimarilerin
        (örneğin MobileNetV4) entegrasyonu hedeflenmektedir.
    </p>
    """
    s1_p2.insert_htmlbox(pymupdf.Rect(50, 50, 545, 790), s1_p2_html)
    doc_s1.save(str(source1_file))
    doc_s1.close()
    created_files["source_1"] = str(source1_file)

    # -------------------------------------------------------------
    # 3. 2.pdf (Kaynak 2) - 1 Sayfa
    # -------------------------------------------------------------
    source2_file = target_path / "2.pdf"
    doc_s2 = pymupdf.open()
    s2_p1 = doc_s2.new_page(width=595, height=842)
    s2_p1_html = f"""
    {base_css}
    <h1>Klinik Metin Özetlemede Yerel Açık Ağırlıklı Modellerin KVKK ve Hız Performansı</h1>
    <div class="meta">
        Selin Yılmaz, Emre Çelik &bull; Tıp Bilişimi Kongresi Bildirileri &bull; 2025
    </div>
    <h2>Bulgular ve Değerlendirme</h2>
    <p>
        Hastanelerdeki epikriz raporları ve klinik notların hızlıca özetlenmesi hekimlerin
        karar süreçlerini hızlandırmaktadır. Bu çalışmada yerel donanımda çalışan açık kaynak
        modeller ile bulut LLM servisleri karşılaştırılmıştır.
    </p>
    <p>
        Bulgularımız göstermektedir ki Ollama üzerinde çalışan yerel açık ağırlıklı modeller
        (Gemma 4), ağ gecikmesini ortadan kaldırdığı için bulut API sistemlerine göre %40 daha
        hızlı yanıt vermektedir. Ayrıca hasta verisi kurum dışına çıkmadığı için KVKK açısından
        klinik kullanıma %100 uygundur.
    </p>
    <p>
        Elde edilen metrikler, hassas sağlık kurumlarında yerel yapay zeka altyapılarının
        güvenli ve sürdürülebilir olduğunu doğrulamaktadır.
    </p>
    """
    s2_p1.insert_htmlbox(pymupdf.Rect(50, 50, 545, 790), s2_p1_html)
    doc_s2.save(str(source2_file))
    doc_s2.close()
    created_files["source_2"] = str(source2_file)

    # 3.pdf BİLEREK ÜRETİLMEDİ (Hayalet Kaynak / AI Halüsinasyonu testi)

    return created_files


if __name__ == "__main__":
    results = create_demo_pdfs()
    print("Demo PDF'leri başarıyla oluşturuldu:")
    for k, v in results.items():
        print(f"  - [{k}]: {v}")
    print("  - [source_3]: 3.pdf bilerek üretilmedi (Hayalet Kaynak Simülasyonu)")
