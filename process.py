# =====================================
# process.py — Movie Search Engine Logic (tối ưu + cache)
# =====================================

import os
import glob
import re
import pandas as pd
import nltk
import spacy
import sqlite3
import pickle
import numpy as np
from functools import lru_cache
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

# =====================================
# Đường dẫn file database & model TF-IDF
# =====================================
DB_PATH = r"checkpoints/movies.db"
VEC_PATH = r"checkpoints/vectorizer.pkl"
MATRIX_PATH = r"checkpoints/tfidf_matrix.pkl"

# =====================================
# Chuẩn bị NLP
# =====================================
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords", quiet=True)

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# =====================================
# Hàm làm sạch văn bản
# =====================================
def clean_text_spacy(text):
    if pd.isna(text):
        return ""
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text.lower())
    doc = nlp(text)
    stop_words = set(stopwords.words("english"))
    tokens = [token.lemma_ for token in doc if token.text not in stop_words and token.text.strip()]
    return " ".join(tokens)

# =====================================
# Load database + TF-IDF model (nếu có)
# =====================================
if os.path.exists(DB_PATH) and os.path.exists(VEC_PATH) and os.path.exists(MATRIX_PATH):
    print("✅ Phát hiện file database & model — load nhanh!")

    conn = sqlite3.connect(DB_PATH)
    combined_df = pd.read_sql_query("SELECT * FROM movies", conn)
    conn.close()

    with open(VEC_PATH, "rb") as f:
        vectorizer = pickle.load(f)
    with open(MATRIX_PATH, "rb") as f:
        tfidf_matrix = pickle.load(f)

else:
    print("⚙️ Không tìm thấy dữ liệu cũ — khởi tạo từ CSV...")

    data_dir = r"D:\Quân\project\movie_query\MovieData"
    all_files = glob.glob(os.path.join(data_dir, "movies_out_*.csv"))
    df_list = [pd.read_csv(f) for f in all_files]
    combined_df = pd.concat(df_list, ignore_index=True)

    print(f"✅ Đã đọc {len(all_files)} file CSV, tổng {len(combined_df)} dòng.")

    combined_df["clean_title"] = combined_df["title"].apply(clean_text_spacy)
    combined_df["clean_plot"] = combined_df["plot"].apply(clean_text_spacy)
    if "genre" in combined_df.columns:
        combined_df["clean_genres"] = combined_df["genre"].apply(clean_text_spacy)
    else:
        combined_df["clean_genres"] = ""

    if "poster" not in combined_df.columns and "poster_url" in combined_df.columns:
        combined_df["poster"] = combined_df["poster_url"]

    title_weight, genre_weight, plot_weight = 3, 2, 1

    def combine_weighted_text(row):
        return (
            (row["clean_title"] + " ") * title_weight
            + (row["clean_genres"] + " ") * genre_weight
            + (row["clean_plot"] + " ") * plot_weight
        )

    combined_df["weighted_text"] = combined_df.apply(combine_weighted_text, axis=1)
    print("✅ Chuẩn bị dữ liệu TF-IDF...")

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(combined_df["weighted_text"])
    print(f"✅ TF-IDF matrix: {tfidf_matrix.shape}")

    conn = sqlite3.connect(DB_PATH)
    combined_df.to_sql("movies", conn, if_exists="replace", index=False)
    conn.close()

    with open(VEC_PATH, "wb") as f:
        pickle.dump(vectorizer, f)
    with open(MATRIX_PATH, "wb") as f:
        pickle.dump(tfidf_matrix, f)

    print("💾 Lưu database & TF-IDF model thành công!")

# =====================================
# Nhận dạng loại truy vấn
# =====================================
def detect_query_type(query, df):
    q = query.lower().strip()

    # 1️⃣ Năm
    if re.search(r"\b(19|20)\d{2}\b", q):
        return "year"

    # 2️⃣ Thể loại
    all_genres = set()
    if "genre" in df.columns:
        for g in df["genre"].dropna():
            for gg in re.split(r"[,/|]+", str(g).lower()):
                gg = gg.strip()
                if gg:
                    all_genres.add(gg)
    if q in all_genres:
        return "genre"

    # 3️⃣ Người (diễn viên/đạo diễn)
    for col in ["cast", "director"]:
        if col in df.columns:
            if any(q in str(x).lower() for x in df[col].dropna().head(3000)):
                return "person"

    # 4️⃣ Tên phim
    if any(q == str(t).lower() for t in df["title"].dropna()):
        return "title"

    # 5️⃣ Mặc định
    return "content"

# =====================================
# Cache hóa bước TF-IDF để tăng tốc độ
# =====================================
@lru_cache(maxsize=256)
def cached_vector_search(query_clean):
    """Trả về chỉ số & điểm cosine_similarity của query đã được vector hóa."""
    query_vec = vectorizer.transform([query_clean])
    cosine_sim = linear_kernel(query_vec, tfidf_matrix).flatten()
    return cosine_sim

# =====================================
# Hàm tìm kiếm thông minh
# =====================================
def smart_search(query, df=combined_df, top_n=10, min_score=0.0):
    query_type = detect_query_type(query, df)
    query_clean = clean_text_spacy(query)
    print(f"🔍 Kiểu truy vấn phát hiện: {query_type}")

    # 1️⃣ Thể loại
    if query_type == "genre" and "genre" in df.columns:
        filtered = df[df["genre"].apply(lambda g: query.lower() in str(g).lower())]
        if not filtered.empty:
            sort_cols = [c for c in ["vote_count", "rating", "popularity"] if c in filtered.columns]
            if sort_cols:
                filtered = filtered.sort_values(by=sort_cols, ascending=False)
            return filtered.head(top_n)

    # 2️⃣ Năm
    if query_type == "year" and "year" in df.columns:
        year_match = re.search(r"\b(19|20)\d{2}\b", query)
        if year_match:
            year = int(year_match.group())
            filtered = df[df["year"] == year]
            sort_cols = [c for c in ["rating", "vote_count", "popularity"] if c in filtered.columns]
            if sort_cols:
                filtered = filtered.sort_values(by=sort_cols, ascending=False)
            return filtered.head(top_n)

    # 3️⃣ Người
    if query_type == "person":
        mask = pd.Series(False, index=df.index)
        for col in ["cast", "director"]:
            if col in df.columns:
                mask |= df[col].apply(lambda c: query.lower() in str(c).lower())
        filtered = df[mask]
        sort_cols = [c for c in ["rating", "vote_count", "popularity"] if c in filtered.columns]
        if sort_cols:
            filtered = filtered.sort_values(by=sort_cols, ascending=False)
        return filtered.head(top_n)

    # 4️⃣ Tên phim
    if query_type == "title":
        filtered = df[df["title"].apply(lambda t: query.lower() in str(t).lower())]
        if not filtered.empty:
            sort_cols = [c for c in ["rating", "vote_count"] if c in filtered.columns]
            if sort_cols:
                filtered = filtered.sort_values(by=sort_cols, ascending=False)
        return filtered.head(top_n)

    # 5️⃣ Nội dung — TF-IDF Similarity (có cache)
    cosine_sim = cached_vector_search(query_clean)
    # Nếu top_n lớn hơn tổng số phim => lấy toàn bộ
    if top_n >= len(cosine_sim):
        top_sorted = np.argsort(cosine_sim)[::-1]  # sắp toàn bộ
    else:
        top_indices = np.argpartition(cosine_sim, -top_n)[-top_n:]
        top_sorted = top_indices[np.argsort(cosine_sim[top_indices])[::-1]]

    results = df.iloc[top_sorted].copy()
    results["similarity_score"] = cosine_sim[top_sorted]

    if "vote_count" in results.columns:
        vc = results["vote_count"].fillna(0).astype(float)
        vc_norm = (vc - vc.min()) / (vc.max() - vc.min() + 1e-9)
        results["combined_score"] = 0.7 * results["similarity_score"] + 0.3 * vc_norm
        results = results.sort_values(by="combined_score", ascending=False)
    else:
        results = results.sort_values(by="similarity_score", ascending=False)

    return results.head(top_n)

print("✅ Module smart_search() + cache đã sẵn sàng!")