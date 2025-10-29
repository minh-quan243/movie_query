# =====================================
# app.py — Flask Web App for Movie Search
# =====================================

from flask import Flask, render_template, request
from process import smart_search, combined_df  # ⚠️ import cả combined_df

app = Flask(__name__)
app.jinja_env.add_extension('jinja2.ext.do')

# =====================================
# Route trang chủ
# =====================================
@app.route('/')
def home():
    # Top 10 phim nổi bật (theo rating + vote_count)
    sort_cols = [c for c in ["rating", "vote_count"] if c in combined_df.columns]
    top_movies = combined_df.sort_values(by=sort_cols, ascending=False).head(10).to_dict(orient='records')

    # Chọn 3 thể loại phổ biến nhất
    genres = ["Action", "Drama", "Comedy", "Animation", "Romance"]
    genre_sections = {}
    for g in genres:
        genre_df = combined_df[combined_df["genre"].apply(lambda x: g.lower() in str(x).lower())]
        genre_sections[g] = genre_df.sort_values(by=sort_cols, ascending=False).head(10).to_dict(orient='records')

    return render_template('index.html', top_movies=top_movies, genre_sections=genre_sections)

# =====================================
# Route xử lý tìm kiếm
# =====================================
@app.route("/search")
def search():
    query = request.args.get("query", "").strip()
    page = int(request.args.get("page", 1))  # 🔹 Lấy số trang (mặc định = 1)
    per_page = 36  # 🔹 Số phim mỗi trang

    # Nếu người dùng chưa nhập gì
    if not query:
        return render_template(
            "results.html",
            query=query,
            results=[],
            page=1,
            total_pages=1,
        )

    # Gọi hàm tìm kiếm — truyền cả DataFrame để tránh NameError
    results = smart_search(query, df=combined_df, top_n=20000)

    # Nếu kết quả rỗng
    if results is None or results.empty:
        return render_template(
            "results.html",
            query=query,
            results=[],
            page=1,
            total_pages=1,
        )

    # Tổng số trang
    total_results = len(results)
    total_pages = max(1, (total_results + per_page - 1) // per_page)

    # Lấy phim trong phạm vi của trang hiện tại
    start = (page - 1) * per_page
    end = start + per_page
    paginated_results = results.iloc[start:end]

    # Chuyển DataFrame sang dict để Jinja render nhanh hơn
    return render_template(
        "results.html",
        query=query,
        results=paginated_results.to_dict(orient="records"),
        page=page,
        total_pages=total_pages,
    )

@app.route('/movie/<movie_id>')
def movie_detail(movie_id):
    movie = combined_df.loc[combined_df["id"] == movie_id].to_dict(orient="records")
    if not movie:
        return render_template("404.html"), 404

    movie = movie[0]

    # Nếu có trailer hoặc YouTube link
    trailer_url = ""
    if "trailer_url" in movie and movie["trailer_url"]:
        trailer_url = movie["trailer_url"]
    elif "trailer" in movie and "youtube.com" in str(movie["trailer"]):
        trailer_url = movie["trailer"]

    # Tìm phim tương tự cùng thể loại hoặc đạo diễn
    similar_movies = []
    if "genre" in movie and movie["genre"]:
        genre = str(movie["genre"]).split(",")[0]
        similar_movies = combined_df[
            combined_df["genre"].apply(lambda x: genre.lower() in str(x).lower())
        ].head(8).to_dict(orient="records")

    return render_template("movie_detail.html", movie=movie, trailer_url=trailer_url, similar_movies=similar_movies)

# =====================================
# Run server
# =====================================
if __name__ == "__main__":
    app.run(debug=True)
