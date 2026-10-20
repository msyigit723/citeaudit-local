"""
CiteAudit Local - PDF & Atıf Ayrıştırıcı Modülü (parser.py)
Hacktoberfest 2026

Bu modül:
1. PyMuPDF ile PDF'lerden sayfa bazlı metin çıkarır.
2. Tez metninden [1], [2] formatındaki iddia cümlelerini ve Kaynakça listesini ayıklar.
3. rank-bm25 ve kelime örtüşmesi (token overlap) ile kaynak PDF içinde en alakalı kanıtları bulur.
"""

from io import BytesIO
from pathlib import Path
import re
from typing import Any, Union
import pymupdf
from rank_bm25 import BM25Okapi


def extract_text_from_pdf(pdf_input: Union[str, Path, bytes, BytesIO]) -> list[dict[str, Any]]:
    """PDF dosyasından sayfa bazlı temizlenmiş metin listesi döndürür.

    Dönüş formatı: [{"page": 1, "text": "sayfa metni..."}, ...]
    """
    pages_data = []

    if isinstance(pdf_input, (str, Path)):
        doc = pymupdf.open(str(pdf_input))
    elif isinstance(pdf_input, bytes):
        doc = pymupdf.open(stream=pdf_input, filetype="pdf")
    elif isinstance(pdf_input, BytesIO):
        doc = pymupdf.open(stream=pdf_input.getvalue(), filetype="pdf")
    else:
        # Streamlit UploadedFile veya dosya benzeri nesne
        doc = pymupdf.open(stream=pdf_input.read(), filetype="pdf")

    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            raw_text = page.get_text()

            # Metin temizleme: birden fazla boşluk ve satır sonu normalizasyonu
            # Unicode ligatürleri düzelt (örn. \ufb01 -> fi, \ufb02 -> fl)
            raw_text = (
                raw_text.replace("\ufb00", "ff")
                .replace("\ufb01", "fi")
                .replace("\ufb02", "fl")
                .replace("\ufb03", "ffi")
                .replace("\ufb04", "ffl")
            )
            lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
            cleaned_text = " ".join(lines)
            cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

            pages_data.append({
                "page": page_num + 1,
                "text": cleaned_text,
                "raw_text": raw_text
            })
    finally:
        doc.close()

    return pages_data


def split_into_sentences(text: str) -> list[str]:
    """Türkçe kısaltmaları ve ondalık sayıları bozmadan metni cümlelere ayırır."""
    if not text:
        return []

    # Ondalık sayıları korumak için geçici maskeleme (örn: %94,2 veya 3.14)
    masked = re.sub(r"(\d+)[.,](\d+)", r"\1__DECIMAL__\2", text)

    # Yaygın akademik kısaltmaları koruma
    abbreviations = [
        "Dr.", "Prof.", "Doç.", "Yrd.", "Arş.", "Gör.", "Uzm.",
        "vb.", "vs.", "örn.", "bkz.", "vd.", "s.", "no.", "vol."
    ]
    for abb in abbreviations:
        replacement = abb.replace(".", "__DOT__")
        masked = re.sub(re.escape(abb), replacement, masked, flags=re.IGNORECASE)

    # Cümle sonu noktası, soru işareti veya ünlemden sonra boşluk gelen yerlerden böl
    raw_sentences = re.split(r"(?<=[.!?])\s+", masked)

    clean_sentences = []
    for s in raw_sentences:
        # Maskeleri geri çevir
        unmasked = s.replace("__DECIMAL__", ",").replace("__DOT__", ".")
        unmasked = re.sub(r"\s+", " ", unmasked).strip()
        if unmasked:
            clean_sentences.append(unmasked)

    return clean_sentences


def extract_claims_and_references(pages: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Tez sayfalarından [1], [2] formatındaki iddia cümlelerini ve Kaynakça'yı ayıklar.

    Dönüş:
    - claims: [{"ref_id": "1", "claim_sentence": "...", "page": 1}, ...]
    - references: {"1": "Kaya, A., & Demir...", "2": "..."}
    """
    ref_heading_regex = re.compile(
        r"(?:^|\n|\s)(KAYNAKÇA|KAYNAKLAR|REFERENCES|BIBLIOGRAPHY)(?:\s|:|$)",
        re.IGNORECASE
    )

    split_page_idx = -1
    split_pos_in_page = -1

    # Kaynakça başlığının nerede başladığını tespit et
    for idx, p in enumerate(pages):
        raw = p.get("raw_text", p["text"])
        match = ref_heading_regex.search(raw)
        if match:
            split_page_idx = idx
            split_pos_in_page = match.start()
            break

    body_pages = []
    references_text = ""

    if split_page_idx != -1:
        # Başlıktan önceki sayfalar tam gövde
        for idx in range(split_page_idx):
            body_pages.append(pages[idx])

        # Başlığın olduğu sayfayı ikiye böl
        split_page = pages[split_page_idx]
        raw = split_page.get("raw_text", split_page["text"])
        body_part = raw[:split_pos_in_page]
        ref_part = raw[split_pos_in_page:]

        body_pages.append({
            "page": split_page["page"],
            "text": re.sub(r"\s+", " ", body_part).strip(),
            "raw_text": body_part
        })

        ref_texts = [ref_part]
        for idx in range(split_page_idx + 1, len(pages)):
            ref_texts.append(pages[idx].get("raw_text", pages[idx]["text"]))
        references_text = "\n".join(ref_texts)
    else:
        # Başlık bulunamadıysa tüm sayfaları gövde kabul et
        body_pages = pages

    # 1. Kaynakça Sözlüğünü Oluşturma
    references_dict: dict[str, str] = {}
    if references_text:
        # [1] Açıklama... formatını yakala
        matches = list(re.finditer(r"\[(\d+)\]\s*([^\[]+)", references_text))
        for m in matches:
            ref_id = m.group(1).strip()
            ref_desc = re.sub(r"\s+", " ", m.group(2)).strip()
            references_dict[ref_id] = ref_desc

    # 2. Gövde Metnindeki Atıf İddialarını Çıkarma
    claims: list[dict[str, Any]] = []
    citation_regex = re.compile(r"\[(\d+)\]")

    for p in body_pages:
        sentences = split_into_sentences(p["text"])
        for sentence in sentences:
            cite_matches = citation_regex.findall(sentence)
            if cite_matches:
                for ref_id in cite_matches:
                    claims.append({
                        "ref_id": ref_id,
                        "claim_sentence": sentence.strip(),
                        "page": p["page"]
                    })

    return claims, references_dict


def tokenize_text(text: str) -> list[str]:
    """Metni arama için küçük harfe ve temiz token dizisine dönüştürür."""
    # Türkçe küçük harf dönüşümü
    lowered = text.replace("İ", "i").replace("I", "ı").lower()
    tokens = re.findall(r"\b[a-zçğışöü0-9,%]{2,}\b", lowered)
    return tokens


def find_best_evidence_in_source_pdf(
    claim: str,
    source_pages: list[dict[str, Any]],
    top_k: int = 2
) -> list[dict[str, Any]]:
    """Kaynak PDF sayfalarını 2-3 cümlelik chunk'lara bölerek

    BM25 ve token örtüşmesi ile iddiayı en çok ilgilendiren kanıtları bulur.
    """
    if not source_pages:
        return []

    # 1. Kaynak PDF sayfalarını 2-3 cümlelik parçalara böl
    chunks: list[dict[str, Any]] = []
    for page_info in source_pages:
        p_num = page_info["page"]
        sentences = split_into_sentences(page_info["text"])
        if not sentences:
            continue

        step = 2
        for i in range(0, len(sentences), step):
            window = sentences[i:i + 3]
            chunk_text = " ".join(window).strip()
            if chunk_text:
                chunks.append({
                    "page": p_num,
                    "text": chunk_text,
                    "tokens": tokenize_text(chunk_text)
                })

    if not chunks:
        return []

    # 2. BM25 Modeli Oluşturma
    corpus_tokens = [c["tokens"] for c in chunks]
    bm25 = BM25Okapi(corpus_tokens)

    claim_tokens = tokenize_text(claim)
    if not claim_tokens:
        return chunks[:top_k]

    bm25_scores = bm25.get_scores(claim_tokens)

    # 3. Kelime Örtüşmesi (Token Overlap) ile Hibrit Puanlama
    claim_token_set = set(claim_tokens)
    scored_chunks = []

    for idx, chunk in enumerate(chunks):
        bm_score = float(bm25_scores[idx]) if idx < len(bm25_scores) else 0.0

        # Jaccard / Overlap skoru
        chunk_token_set = set(chunk["tokens"])
        overlap_count = len(claim_token_set.intersection(chunk_token_set))
        overlap_score = overlap_count / max(len(claim_token_set), 1)

        # Sayı veya yüzde eşleşmesi varsa ek ağırlık ver (%94,2 vb.)
        numeric_matches = set(re.findall(r"\b\d+[.,]?\d*%", claim)).intersection(
            set(re.findall(r"\b\d+[.,]?\d*%", chunk["text"]))
        )
        bonus = 3.0 if numeric_matches else 0.0

        final_score = bm_score + (overlap_score * 5.0) + bonus

        scored_chunks.append({
            "page": chunk["page"],
            "text": chunk["text"],
            "score": round(final_score, 4),
            "overlap_ratio": round(overlap_score, 3)
        })

    # Skora göre azalan sırala
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    return scored_chunks[:top_k]
