"""
CiteAudit Local - Doğrulama ve Jüri Kriterleri Test Scripti
Tüm modülleri uçtan uca test eder ve 4 iddianın doğru kategorilere düştüğünü doğrular.
"""

import sys
from pathlib import Path

# UTF-8 stdout desteği
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import generate_demo_pdfs
import parser
import verifier
from app import execute_audit, generate_markdown_report


def run_full_pipeline_test():
    print("=" * 65)
    print("🛡️ CITEAUDIT LOCAL - UÇTAN UCA DOĞRULAMA TESTİ BAŞLATILIYOR")
    print("=" * 65)

    # 1. Demo PDF'leri Üret
    print("\n[Adım 1] Demo PDF'leri üretiliyor...")
    pdf_files = generate_demo_pdfs.create_demo_pdfs("sample_data")
    assert Path("sample_data/Tez_Taslagi.pdf").exists(), "Tez_Taslagi.pdf bulunamadı!"
    assert Path("sample_data/1.pdf").exists(), "1.pdf bulunamadı!"
    assert Path("sample_data/2.pdf").exists(), "2.pdf bulunamadı!"
    assert not Path("sample_data/3.pdf").exists(), "3.pdf bilerek olmamalıydı!"
    print("✓ Demo PDF'leri doğrulandı (1.pdf, 2.pdf mevcut; 3.pdf hayalet kaynak olarak yok).")

    # 2. Ayrıştırma Testi
    print("\n[Adım 2] PDF ayrıştırma ve atıf ayıklama...")
    pages = parser.extract_text_from_pdf("sample_data/Tez_Taslagi.pdf")
    claims, refs = parser.extract_claims_and_references(pages)
    print(f"✓ Ayıklanan İddia Sayısı: {len(claims)}")
    print(f"✓ Ayıklanan Kaynakça Sayısı: {len(refs)}")
    assert len(claims) == 4, f"Beklenen 4 iddia, bulunan: {len(claims)}"
    assert len(refs) == 3, f"Beklenen 3 referans, bulunan: {len(refs)}"

    # 3. Denetim Boru Hattı Testi
    print("\n[Adım 3] Atıf Doğrulama & NLI & Crossref Motoru çalıştırılıyor...")
    sources_map = {
        "1": Path("sample_data/1.pdf"),
        "2": Path("sample_data/2.pdf")
    }

    # Streamlit bağımsız denetim testi
    audit_results = []
    parsed_sources = {
        "1": parser.extract_text_from_pdf("sample_data/1.pdf"),
        "2": parser.extract_text_from_pdf("sample_data/2.pdf")
    }

    for c in claims:
        ref_id = str(c["ref_id"])
        sentence = c["claim_sentence"]
        ref_text = refs.get(ref_id, "")

        if ref_id in parsed_sources:
            evidence = parser.find_best_evidence_in_source_pdf(sentence, parsed_sources[ref_id], top_k=2)
            res = verifier.verify_claim_with_gemma(sentence, evidence, model_name="fallback")
            audit_results.append({
                "ref_id": ref_id,
                "ref_text": ref_text,
                "claim_sentence": sentence,
                "claim_page": c["page"],
                "verdict": res["verdict"],
                "confidence": res["confidence"],
                "evidence_page": res.get("page", 1),
                "evidence_quote": res.get("evidence_quote", ""),
                "explanation": res.get("explanation", ""),
                "suggested_fix": res.get("suggested_fix", "")
            })
        else:
            # 3.pdf yok -> Crossref sorgusu
            crossref_status = verifier.check_paper_exists_online(ref_text)
            is_ghost = not crossref_status.get("exists", False)
            verdict = "GHOST_CITATION" if is_ghost else "NOT_FOUND"
            audit_results.append({
                "ref_id": ref_id,
                "ref_text": ref_text,
                "claim_sentence": sentence,
                "claim_page": c["page"],
                "verdict": verdict,
                "confidence": 100,
                "evidence_page": c["page"],
                "evidence_quote": "Kaynak PDF yok ve Crossref'te bulunamadı.",
                "explanation": "AI Halüsinasyonu (Uydurma Kaynak)",
                "suggested_fix": "Geçerli bir referans ile değiştirilmelidir."
            })

    verdicts = [r["verdict"] for r in audit_results]
    print("\nSonuç Kararları:")
    for i, r in enumerate(audit_results, 1):
        print(f"  [{i}] Atıf [{r['ref_id']}]: {r['verdict']} (%{r['confidence']})")
        print(f"      İddia: {r['claim_sentence'][:65]}...")
        print(f"      Hakem Notu: {r['explanation'][:75]}...")

    # Beklenen 4 kategori kontrolü
    assert verdicts[0] == "SUPPORTED", f"1. İddia SUPPORTED olmalıydı, {verdicts[0]} geldi"
    assert verdicts[1] == "CONTRADICTED", f"2. İddia CONTRADICTED olmalıydı, {verdicts[1]} geldi"
    assert verdicts[2] == "NOT_FOUND", f"3. İddia NOT_FOUND olmalıydı, {verdicts[2]} geldi"
    assert verdicts[3] == "GHOST_CITATION", f"4. İddia GHOST_CITATION olmalıydı, {verdicts[3]} geldi"

    print("\n✓ TÜM 4 JÜRİ SENARYOSU BAŞARIYLA DOĞRULANDI:")
    print("  1. 🟢 SUPPORTED (Doğru Atıf)")
    print("  2. 🔴 CONTRADICTED (Çarpıtılmış / Çelişen Atıf)")
    print("  3. 🟡 NOT_FOUND (Bağlam Dışı Atıf)")
    print("  4. 🚨 GHOST_CITATION (Hayalet / AI Uydurması Kaynak)")

    # 4. Rapor Üretimi Testi
    stats = {
        "total": len(audit_results),
        "supported": verdicts.count("SUPPORTED"),
        "contradicted": verdicts.count("CONTRADICTED"),
        "not_found": verdicts.count("NOT_FOUND"),
        "ghost": verdicts.count("GHOST_CITATION"),
        "score": (verdicts.count("SUPPORTED") / len(audit_results)) * 100
    }
    report = generate_markdown_report(audit_results, stats)
    assert "# 🛡️ CITEAUDIT LOCAL" in report, "Rapor başlığı eksik!"
    print(f"\n✓ Markdown Hakem Raporu başarıyla üretildi ({len(report)} karakter).")

    print("\n" + "=" * 65)
    print("🎉 TÜM DOĞRULAMA TESTLERİ %100 BAŞARIYLA TAMAMLANDI!")
    print("=" * 65)


if __name__ == "__main__":
    run_full_pipeline_test()
