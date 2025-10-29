// ============================
// 🎬 Movie Carousel Script
// ============================

document.addEventListener("DOMContentLoaded", () => {
    const carousels = document.querySelectorAll(".carousel-container");

    carousels.forEach(container => {
        const movieRow = container.querySelector(".movie-row");
        const leftBtn = container.querySelector(".nav-btn.left");
        const rightBtn = container.querySelector(".nav-btn.right");
        const cardWidth = movieRow.querySelector(".movie-card").offsetWidth + 15; // thêm khoảng cách

        // =============================
        // 👉 Nút chuyển trái/phải
        // =============================
        leftBtn.addEventListener("click", () => {
            movieRow.scrollBy({ left: -cardWidth * 3, behavior: "smooth" });
        });

        rightBtn.addEventListener("click", () => {
            movieRow.scrollBy({ left: cardWidth * 3, behavior: "smooth" });
        });

        // =============================
        // 🔁 Auto Slide Loop
        // =============================
        let autoSlide = setInterval(() => {
            const maxScrollLeft = movieRow.scrollWidth - movieRow.clientWidth;

            if (Math.abs(movieRow.scrollLeft - maxScrollLeft) < 5) {
                // Nếu đến cuối → quay về đầu
                movieRow.scrollTo({ left: 0, behavior: "smooth" });
            } else {
                // Trượt tiếp
                movieRow.scrollBy({ left: cardWidth * 3, behavior: "smooth" });
            }
        }, 4000); // 4 giây trượt một lần

        // Dừng auto khi hover để xem phim
        container.addEventListener("mouseenter", () => clearInterval(autoSlide));
        container.addEventListener("mouseleave", () => {
            autoSlide = setInterval(() => {
                const maxScrollLeft = movieRow.scrollWidth - movieRow.clientWidth;
                if (Math.abs(movieRow.scrollLeft - maxScrollLeft) < 5) {
                    movieRow.scrollTo({ left: 0, behavior: "smooth" });
                } else {
                    movieRow.scrollBy({ left: cardWidth * 3, behavior: "smooth" });
                }
            }, 4000);
        });
    });
});
