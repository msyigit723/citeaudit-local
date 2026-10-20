"""
CiteAudit Local - Web Kullanıcı Arayüzü (app.py)
Hacktoberfest 2026

Modern, SaaS görünümlü Streamlit denetim arayüzü:
- Çevrimdışı ve Hibrit Mod
- Tek tıkla jüri demosu çalıştırma
- Manuel PDF yükleme ve analizi
- KPI metrik kartları ve renk kodlu hakem değerlendirmeleri
- İndirilebilir Markdown Hakem Denetim Raporu
"""

from datetime import datetime
import os
from pathlib import Path
import re
import streamlit as st

import parser
import verifier

# Sayfa Konfigürasyonu
st.set_page_config(
    page_title="CiteAudit Local - Akademik Atıf & Halüsinasyon Denetçisi",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern SaaS Arayüz Stilleri (Custom CSS)
st.markdown("""
<style>
    /* Ana Font ve Arka Plan */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%);
        padding: 30px 35px;
        border-radius: 18px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
    }
    
    .main-header h1 {
        color: #ffffff;
        font-weight: 800;
        font-size: 2.2rem;
        margin: 0 0 10px 0;
        letter-spacing: -0.5px;
    }
    
    .main-header p {
        color: #cbd5e1;
        font-size: 1.05rem;
        margin: 0;
        max-width: 900px;
        line-height: 1.5;
    }
    
    .info-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #4f46e5;
        padding: 18px 22px;
        border-radius: 12px;
        margin-bottom: 25px;
        font-size: 0.95rem;
        color: #334155;
    }
    
    .info-card strong {
        color: #1e1b4b;
    }
    
    /* KPI Kartları */
    .metric-container {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 12px;
        margin-bottom: 25px;
    }
    
    .metric-card {
        background: white;
        padding: 16px 14px;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
    }
    
    .metric-val {
        font-size: 1.8rem;
        font-weight: 800;
        margin: 4px 0;
    }
    
    .metric-lbl {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748b;
    }
    
    /* Rozetler */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.3px;
    }
    .badge-supported { background-color: #dcfce7; color: #15803d; border: 1px solid #86efac; }
    .badge-contradicted { background-color: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
    .badge-notfound { background-color: #fef9c3; color: #a16207; border: 1px solid #fde047; }
    .badge-ghost { background-color: #f3e8ff; color: #6b21a8; border: 1px solid #d8b4fe; }
    
    /* Revizyon Kutusu */
    .revision-box {
        background-color: #eff6ff;
        border: 1px dashed #3b82f6;
        border-radius: 10px;
        padding: 14px 18px;
        margin-top: 10px;
        font-size: 0.92rem;
        color: #1e3a8a;
    }
    
    /* Buton İyileştirmeleri */
    div.stButton > button {
        border-radius: 10px;
        font-weight: 700;
        padding: 12px 24px;
        transition: all 0.2s ease;
    }
</style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------
# SIDEBAR
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🛡️ CiteAudit Local")
    st.caption("v1.0.0 • Hacktoberfest 2026 Special")
    st.divider()

    st.markdown("#### ⚙️ Denetim Yapılandırması")

    # Çalışma Modu
    operating_mode = st.radio(
        "Çalışma Modu:",
        [
            "🔒 %100 Çevrimdışı (Gizli Tez & TÜBİTAK Modu)",
            "🌐 Hibrit Mod (Yerel RAG + Crossref Hayalet Kaynak Avcısı)"
        ],
        index=1,
        help="Çevrimdışı modda hiçbir harici ağ çağrısı yapılmaz. Hibrit modda sahte yayın tespiti için Crossref sorgusu çalıştırılır."
    )
    is_offline_mode = "Çevrimdışı" in operating_mode

    # Model Seçimi
    available_models = verifier.get_available_ollama_models()
    selected_model = st.selectbox(
        "Doğrulama Motoru (Ollama):",
        options=available_models,
        index=0,
        help="Yerel makinenizde çalışan Ollama açık ağırlıklı dil modelleri."
    )

    if "Fallback Mode" in selected_model:
        st.warning("⚠️ Ollama çevrimdışı. Kural tabanlı Acil Fallback Doğrulayıcısı devrede!")
    else:
        st.success(f"🟢 Motor Hazır: {selected_model}")

    # Sentry Entegrasyonu
    st.markdown("#### 📡 Gözlem & İzleme (Sentry)")
    sentry_dsn = st.text_input(
        "Sentry DSN (Opsiyonel):",
        value=os.getenv("SENTRY_DSN", ""),
        type="password",
        placeholder="https://...@sentry.io/..."
    )
    if sentry_dsn:
        if verifier.init_sentry(sentry_dsn):
            st.success("🟢 Sentry Agent Tracing Aktif")
        else:
            st.error("🔴 Sentry başlatılamadı.")

    st.divider()

    # Manuel Dosya Yükleyiciler
    st.markdown("#### 📂 Manuel PDF Yükleme")
    uploaded_thesis = st.file_uploader(
        "1. Tez / Makale Taslağı (PDF):",
        type=["pdf"],
        help="İçinde [1], [2] atıfları ve Kaynakça bulunan ana belge."
    )
    uploaded_sources = st.file_uploader(
        "2. Kaynak Yayınlar (Çoklu PDF):",
        type=["pdf"],
        accept_multiple_files=True,
        help="Kaynakça ile eşleşen kaynak PDF dosyaları (örn. 1.pdf, 2.pdf)."
    )
    st.caption("İpucu: Kaynak dosyaların adını referans numarası yapabilirsiniz (örn: 1.pdf).")


# -------------------------------------------------------------
# ANA EKRAN ÜST BAR
# -------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>🛡️ CiteAudit Local</h1>
    <p>
        Çevrimdışı Akademik Atıf, Bağlam Çarpıtma ve AI Halüsinasyon Denetçisi.
        Yüksek lisans/doktora tezlerinde ve hakemli makalelerde kaynakça çarpıtmalarını,
        yanıltıcı alıntıları ve yapay zeka tarafından uydurulan hayalet referansları anında denetleyin.
    </p>
</div>
""", unsafe_allow_html=True)

# "Why Local Open-Weight AI?" Bilgi Kutusu
st.markdown("""
<div class="info-card">
    <strong>💡 Neden Yerel Açık Ağırlıklı Yapay Zeka (Local Open-Weight AI)?</strong><br>
    <ul>
        <li><strong>Yayın Etiği ve Çift Kör Hakemlik:</strong> Henüz yayımlanmamış tez taslakları veya gizli hakem raporları üçüncü taraf bulut API sağlayıcılarına sızdırılamaz.</li>
        <li><strong>Telifli PDF Koruması:</strong> IEEE, Elsevier veya Springer gibi lisanslı veri tabanlarından indirilen makaleler dış sunuculara yüklenmeden yerel donanımda işlenir.</li>
        <li><strong>Sıfır Maliyet & Kesintisiz Güvenilirlik:</strong> Token başına API ücreti olmadan, Ollama & Gemma 4 ile %100 yerel ve sınırsız denetim sağlanır.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Aksiyon Butonları
btn_col1, btn_col2 = st.columns(2)

run_demo = btn_col1.button(
    "🚀 Tek Tıkla Örnek Jüri Demosunu Çalıştır (sample_data/)",
    use_container_width=True,
    type="primary"
)

run_custom = btn_col2.button(
    "🔍 Yüklenen Dosyaları Denetle",
    use_container_width=True,
    disabled=not (uploaded_thesis is not None)
)


# -------------------------------------------------------------
# DENETİM ÇALIŞTIRMA MOTORU
# -------------------------------------------------------------
def execute_audit(thesis_input, source_files_dict, is_offline: bool, model: str):
    """Tez ve kaynak belgelerini denetler ve sonuçları üretir."""
    # 1. Tez metnini çıkar
    thesis_pages = parser.extract_text_from_pdf(thesis_input)
    if not thesis_pages:
        st.error("Tez PDF'inden metin okunamadı!")
        return None

    # 2. İddiaları ve Kaynakça'yı ayıkla
    claims, references = parser.extract_claims_and_references(thesis_pages)
    if not claims:
        st.warning("Belgede [1], [2] formatında hiçbir atıf cümlesi tespit edilemedi!")
        return None

    # 3. Kaynak PDF'leri belleğe al
    parsed_sources = {}
    for ref_key, src_file in source_files_dict.items():
        try:
            parsed_sources[str(ref_key)] = parser.extract_text_from_pdf(src_file)
        except Exception as e:
            st.error(f"Kaynak PDF '{ref_key}' okunamadı: {e}")

    audit_results = []
    progress_bar = st.progress(0, text="Atıflar analiz ediliyor...")

    for idx, claim in enumerate(claims):
        ref_id = str(claim["ref_id"])
        ref_text = references.get(ref_id, f"[{ref_id}] (Kaynakçada tanım bulunamadı)")
        sentence = claim["claim_sentence"]
        claim_page = claim["page"]

        progress_text = f"Denetleniyor ({idx+1}/{len(claims)}): Atıf [{ref_id}]..."
        progress_bar.progress((idx) / len(claims), text=progress_text)

        # Kaynak PDF var mı?
        source_pages = parsed_sources.get(ref_id)

        if source_pages:
            # Kaynak PDF mevcut: BM25 ile kanıt bul ve Gemma ile doğrula
            evidence = parser.find_best_evidence_in_source_pdf(sentence, source_pages, top_k=2)
            nli_result = verifier.verify_claim_with_gemma(sentence, evidence, model_name=model)

            audit_results.append({
                "ref_id": ref_id,
                "ref_text": ref_text,
                "claim_sentence": sentence,
                "claim_page": claim_page,
                "verdict": nli_result.get("verdict", "NOT_FOUND"),
                "confidence": nli_result.get("confidence", 85),
                "evidence_page": nli_result.get("page", evidence[0]["page"] if evidence else 1),
                "evidence_quote": nli_result.get("evidence_quote", ""),
                "explanation": nli_result.get("explanation", ""),
                "suggested_fix": nli_result.get("suggested_fix", "")
            })
        else:
            # Kaynak PDF klasörde yok!
            # Çevrimdışı mod değilse Crossref'ten sorgula
            crossref_status = {}
            if not is_offline:
                crossref_status = verifier.check_paper_exists_online(ref_text)

            is_ghost = False
            if is_offline:
                # Çevrimdışı modda kaynak PDF yoksa şüpheli/eksik kaynak
                is_ghost = True
                ghost_reason = "Kaynak PDF dosyası sağlanmadı (Çevrimdışı mod)."
            else:
                # Hibrit modda: Dosya yok + Crossref'te eşleşme yoksa hayalet kaynak
                if not crossref_status.get("exists", False):
                    is_ghost = True
                    ghost_reason = crossref_status.get("reason", "Crossref veritabanında bulunamadı.")
                else:
                    is_ghost = False

            if is_ghost:
                audit_results.append({
                    "ref_id": ref_id,
                    "ref_text": ref_text,
                    "claim_sentence": sentence,
                    "claim_page": claim_page,
                    "verdict": "GHOST_CITATION",
                    "confidence": 100,
                    "evidence_page": claim_page,
                    "evidence_quote": "Kaynak PDF dosyası sağlanmadı ve uluslararası akademik indekslerde (Crossref) makale kaydına ulaşılamadı.",
                    "explanation": f"🚨 AI Halüsinasyonu Tespit Edildi: Bu atıf akademik literatürde doğrulanabilir bir karşılığa sahip değildir. ({ghost_reason})",
                    "suggested_fix": "Yapay zeka tarafından uydurulan hayalet kaynak tezden çıkarılmalı veya doğrulanabilir gerçek bir yayın ile değiştirilmelidir."
                })
            else:
                audit_results.append({
                    "ref_id": ref_id,
                    "ref_text": ref_text,
                    "claim_sentence": sentence,
                    "claim_page": claim_page,
                    "verdict": "NOT_FOUND",
                    "confidence": 75,
                    "evidence_page": claim_page,
                    "evidence_quote": f"Makale Crossref üzerinde doğrulandı ancak kaynak PDF yüklenmedi ({crossref_status.get('matched_title', '')}).",
                    "explanation": "Makale kaydı literatürde mevcut fakat tam metin PDF sunulmadığı için iddia cümlesi kanıtla eşleştirilemedi.",
                    "suggested_fix": f"Lütfen denetimin tamamlanabilmesi için '{ref_id}.pdf' dosyasını yükleyin."
                })

    progress_bar.progress(1.0, text="Denetim tamamlandı!")
    return audit_results


def generate_markdown_report(results: list[dict], stats: dict) -> str:
    """Hakem Denetim Raporunu Markdown formatında oluşturur."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = f"""# 🛡️ CITEAUDIT LOCAL - AKADEMİK ATIF & HALÜSİNASYON DENETİM RAPORU
*Oluşturulma Tarihi:* {now}  
*Denetim Motoru:* Gemma 4 (Yerel NLI) & Crossref Bibliyografik Doğrulama  
*Etik / Gizlilik:* %100 Yerel İşlem (Double-Blind Peer Review Uyumlu)

---

## 📊 GENEL DENETİM İSTATİSTİKLERİ
- **Toplam İncelenen Atıf:** {stats['total']}
- **🟢 Doğrulanan Atıflar:** {stats['supported']}
- **🔴 Çelişen / Çarpıtılmış Atıflar:** {stats['contradicted']}
- **🟡 Bağlam Dışı / Kanıtsız Atıflar:** {stats['not_found']}
- **🚨 Hayalet Kaynaklar (AI Halüsinasyonu):** {stats['ghost']}
- **🏆 Akademik Güven Skoru:** %{stats['score']:.1f}

---

## 📑 ATIF BAZLI AYRINTILI HAKEM RAPORU

"""
    for idx, r in enumerate(results, 1):
        v = r["verdict"]
        badge_text = {
            "SUPPORTED": "🟢 DOĞRULANDI (SUPPORTED)",
            "CONTRADICTED": "🔴 ÇELİŞEN / ÇARPITILMIŞ (CONTRADICTED)",
            "NOT_FOUND": "🟡 BAĞLAM DIŞI (NOT_FOUND)",
            "GHOST_CITATION": "🚨 HAYALET KAYNAK / AI HALÜSİNASYONU (GHOST)"
        }.get(v, v)

        report += f"### {idx}. İddia [Atıf {r['ref_id']}] - {badge_text}\n"
        report += f"- **Tezdeki İddia (Sayfa {r['claim_page']}):** \"{r['claim_sentence']}\"\n"
        report += f"- **Kaynakça Kaydı:** {r['ref_text']}\n"
        report += f"- **Hakem Güven Oranı:** %{r['confidence']}\n"
        report += f"- **Kaynak Belge Kanıtı (Sayfa {r['evidence_page']}):** \"{r['evidence_quote']}\"\n"
        report += f"- **Hakem Değerlendirmesi:** {r['explanation']}\n"

        if r.get("suggested_fix"):
            report += f"- **💡 Gemma 4 Revizyon Önerisi:** *{r['suggested_fix']}*\n"

        report += "\n---\n\n"

    report += """
*Bu rapor CiteAudit Local tarafından açık ağırlıklı yerel yapay zeka ve deterministik bilgi alma (BM25) modelleri kullanılarak bağımsız olarak üretilmiştir.*
"""
    return report


# -------------------------------------------------------------
# ÇALIŞTIRMA TETİKLEYİCİSİ
# -------------------------------------------------------------
if run_demo:
    # Demo PDF'lerinin varlığını kontrol et, yoksa oluştur
    demo_thesis_path = Path("sample_data/Tez_Taslagi.pdf")
    if not demo_thesis_path.exists():
        with st.spinner("Örnek demo PDF'leri üretiliyor..."):
            import generate_demo_pdfs
            generate_demo_pdfs.create_demo_pdfs("sample_data")

    # Kaynakları hazırla
    sources_map = {}
    if Path("sample_data/1.pdf").exists():
        sources_map["1"] = Path("sample_data/1.pdf")
    if Path("sample_data/2.pdf").exists():
        sources_map["2"] = Path("sample_data/2.pdf")
    # 3.pdf bilerek yok

    with st.spinner("Jüri Demosu Denetleniyor (Yerel RAG + NLI)..."):
        results = execute_audit(
            thesis_input=str(demo_thesis_path),
            source_files_dict=sources_map,
            is_offline=is_offline_mode,
            model=selected_model
        )
        st.session_state["audit_results"] = results
        st.session_state["audit_title"] = "Jüri Demosu (Tez_Taslagi.pdf)"

elif run_custom and uploaded_thesis:
    # Manuel yüklenen dosyaları hazırla
    sources_map = {}
    for src in uploaded_sources:
        # Dosya adından referans ID'si çıkarmaya çalış (örn: 1.pdf -> 1)
        m = re.search(r"(\d+)", src.name)
        if m:
            sources_map[m.group(1)] = src
        else:
            sources_map[src.name] = src

    with st.spinner("Yüklenen Belgeler Denetleniyor..."):
        results = execute_audit(
            thesis_input=uploaded_thesis,
            source_files_dict=sources_map,
            is_offline=is_offline_mode,
            model=selected_model
        )
        st.session_state["audit_results"] = results
        st.session_state["audit_title"] = uploaded_thesis.name


# -------------------------------------------------------------
# SONUÇ EKRANI
# -------------------------------------------------------------
if "audit_results" in st.session_state and st.session_state["audit_results"]:
    results = st.session_state["audit_results"]

    # İstatistikleri hesapla
    total_claims = len(results)
    supported_cnt = sum(1 for r in results if r["verdict"] == "SUPPORTED")
    contradicted_cnt = sum(1 for r in results if r["verdict"] == "CONTRADICTED")
    notfound_cnt = sum(1 for r in results if r["verdict"] == "NOT_FOUND")
    ghost_cnt = sum(1 for r in results if r["verdict"] == "GHOST_CITATION")

    # Akademik Güven Skoru
    # (Doğrulananlar tam puan, Çelişen/Hayaletler ağır eksi puan)
    score = max(0.0, min(100.0, (supported_cnt / total_claims) * 100)) if total_claims > 0 else 0.0

    stats = {
        "total": total_claims,
        "supported": supported_cnt,
        "contradicted": contradicted_cnt,
        "not_found": notfound_cnt,
        "ghost": ghost_cnt,
        "score": score
    }

    st.markdown(f"### 📋 Denetim Özeti: `{st.session_state.get('audit_title', 'Belge')}`")

    # KPI Metrik Kartları
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5, kpi_col6 = st.columns(6)

    kpi_col1.metric("Toplam Atıf", f"{total_claims}")
    kpi_col2.metric("🟢 Doğrulanan", f"{supported_cnt}")
    kpi_col3.metric("🔴 Çelişen", f"{contradicted_cnt}")
    kpi_col4.metric("🟡 Bağlam Dışı", f"{notfound_cnt}")
    kpi_col5.metric("🚨 Hayalet Kaynak", f"{ghost_cnt}")
    kpi_col6.metric("Akademik Güven", f"%{score:.1f}")

    st.divider()

    # Ayrıntılı Kartlar
    st.markdown("### 🔍 İncelenen Atıflar ve Hakem Bulguları")

    badge_classes = {
        "SUPPORTED": ("badge-supported", "🟢 DOĞRULANDI"),
        "CONTRADICTED": ("badge-contradicted", "🔴 ÇELİŞEN / ÇARPITILMIŞ ATIF"),
        "NOT_FOUND": ("badge-notfound", "🟡 BAĞLAM DIŞI / KANITSIZ"),
        "GHOST_CITATION": ("badge-ghost", "🚨 HAYALET KAYNAK (AI HALÜSİNASYONU)")
    }

    for idx, r in enumerate(results, 1):
        v = r["verdict"]
        badge_cls, badge_text = badge_classes.get(v, ("badge-notfound", v))

        expander_title = f"{idx}. [Atıf {r['ref_id']}] {badge_text} - Tez Sayfa {r['claim_page']}"

        with st.expander(expander_title, expanded=(v != "SUPPORTED")):
            col_a, col_b = st.columns([3, 1])

            with col_a:
                st.markdown(f"**📝 Tezdeki İddia Cümlesi:**")
                st.info(f"\"{r['claim_sentence']}\"")

                st.markdown(f"**📚 Kaynakça Bilgisi:**")
                st.caption(f"[{r['ref_id']}] {r['ref_text']}")

            with col_b:
                st.markdown(f"<span class='badge {badge_cls}'>{badge_text}</span>", unsafe_allow_html=True)
                st.markdown(f"**Güven Oranı:** `%{r['confidence']}`")
                st.markdown(f"**Kanıt Sayfası:** `Sayfa {r['evidence_page']}`")

            # Kanıt Alıntısı
            st.markdown("**🔎 Kaynak Belgeden Çıkarılan Birebir Kanıt Alıntısı:**")
            st.code(r["evidence_quote"], language="text")

            # Hakem Açıklaması
            st.markdown(f"**👨‍🏫 Hakem Açıklaması:** {r['explanation']}")

            # Revizyon Önerisi (CONTRADICTED, NOT_FOUND, GHOST_CITATION için)
            if r.get("suggested_fix"):
                st.markdown(f"""
                <div class="revision-box">
                    <strong>💡 Gemma 4 Otomatik Revizyon Önerisi:</strong><br>
                    {r['suggested_fix']}
                </div>
                """, unsafe_allow_html=True)

    # İndirme Butonu
    st.divider()
    report_md = generate_markdown_report(results, stats)

    d_col1, d_col2 = st.columns([1, 3])
    d_col1.download_button(
        label="📥 Hakem Denetim Raporunu İndir (.md)",
        data=report_md,
        file_name=f"CiteAudit_Raporu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown",
        use_container_width=True,
        type="primary"
    )
    d_col2.caption("Bu rapor akademik jüriler, tez danışmanları ve dergi editörleri için standartlaştırılmış NLI doğrulama kanıtlarını içerir.")
