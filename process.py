# =====================================
# 1️⃣ Import thư viện
# =====================================
import os
import glob
import re
import pandas as pd
import nltk
import spacy
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# =====================================
# 2️⃣ Đọc và gộp dữ liệu
# =====================================
data_dir = r"D:\Quân\project\movie_query\MovieData"
all_files = glob.glob(os.path.join(data_dir, "movies_out_*.csv"))

df_list = [pd.read_csv(f) for f in all_files]
combined_df = pd.concat(df_list, ignore_index=True)

print(f"✅ Đã đọc {len(all_files)} file CSV, tổng {len(combined_df)} dòng.")

# =====================================
# 3️⃣ Chuẩn bị NLP
# =====================================
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# =====================================
# 4️⃣ Hàm làm sạch văn bản
# =====================================
def clean_text_spacy(text):
    if pd.isna(text):
        return ""
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())
    doc = nlp(text)
    stop_words = set(stopwords.words('english'))
    tokens = [token.lemma_ for token in doc if token.text not in stop_words and token.text.strip()]
    return " ".join(tokens)

# =====================================
# 5️⃣ Làm sạch các trường quan trọng
# =====================================
combined_df["clean_title"] = combined_df["title"].apply(clean_text_spacy)
combined_df["clean_plot"] = combined_df["plot"].apply(clean_text_spacy)
if "genre" in combined_df.columns:
    combined_df["clean_genres"] = combined_df["genre"].apply(clean_text_spacy)
else:
    combined_df["clean_genres"] = ""

# Nếu có poster_url thì rename để tiện dùng
if "poster" not in combined_df.columns and "poster_url" in combined_df.columns:
    combined_df["poster"] = combined_df["poster_url"]

# =====================================
# 6️⃣ Tạo văn bản kết hợp có trọng số
# =====================================
title_weight = 3.0
genre_weight = 2.0
plot_weight = 1.0

def combine_weighted_text(row):
    title_part = (row["clean_title"] + " ") * int(title_weight)
    genre_part = (row["clean_genres"] + " ") * int(genre_weight)
    plot_part = (row["clean_plot"] + " ") * int(plot_weight)
    return title_part + genre_part + plot_part

combined_df["weighted_text"] = combined_df.apply(combine_weighted_text, axis=1)

print("✅ Dữ liệu đã sẵn sàng cho TF-IDF")

# =====================================
# 7️⃣ TF-IDF và tìm kiếm
# =====================================
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(combined_df["weighted_text"])

print(f"✅ TF-IDF matrix có kích thước: {tfidf_matrix.shape}")

def search_tfidf_weighted(query, min_score=0.0):
    """
    🔍 Tìm kiếm phim dựa trên TF-IDF có trọng số cho các trường (title, genres, plot).
    - Không giới hạn số lượng kết quả.
    - Trả về toàn bộ thông tin của phim (kể cả poster).
    - Lọc theo ngưỡng similarity (min_score).
    """
    query_clean = clean_text_spacy(query)
    query_vec = vectorizer.transform([query_clean])
    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()

    # Lọc và sắp xếp theo độ tương đồng giảm dần
    sorted_indices = similarities.argsort()[::-1]
    results = combined_df.iloc[sorted_indices].copy()
    results["similarity_score"] = similarities[sorted_indices]

    # Lọc bỏ phim có điểm quá thấp (nếu muốn)
    results = results[results["similarity_score"] >= min_score]

    return results