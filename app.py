# =====================================
# app.py — Flask Web App for Movie Search
# =====================================

from flask import Flask, render_template, request
from process import search_tfidf_weighted

app = Flask(__name__)

# =====================================
# Route trang chủ
# =====================================
@app.route('/')
def home():
    return render_template('index.html')

# =====================================
# Route xử lý tìm kiếm
# =====================================
@app.route("/search")
def search():
    query = request.args.get("query", "")
    page = int(request.args.get("page", 1))  # 🔹 Lấy số trang (mặc định = 1)
    per_page = 36  # 🔹 Số phim mỗi trang

    # Gọi hàm tìm kiếm
    results = search_tfidf_weighted(query)

    # Tổng số trang
    total_results = len(results)
    total_pages = (total_results + per_page - 1) // per_page

    # Lấy phim trong phạm vi của trang hiện tại
    start = (page - 1) * per_page
    end = start + per_page
    paginated_results = results.iloc[start:end]

    return render_template(
        "results.html",
        query=query,
        results=paginated_results,
        page=page,
        total_pages=total_pages,
    )

if __name__ == "__main__":
    app.run(debug=True)
