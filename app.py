# =====================================
# app.py — Flask Web App for Movie Search
# =====================================

from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from process import smart_search, combined_df
import pandas as pd
import os
import sqlite3
import hashlib
from functools import wraps
from datetime import datetime, timedelta

# Configure Flask to serve React build files
app = Flask(__name__, static_folder='frontend/dist', static_url_path='')
app.secret_key = 'dev-secret-key-change-in-production'  # WARNING: Change in production!
CORS(app, supports_credentials=True, origins=['http://localhost:5173', 'http://127.0.0.1:8000'])  # Enable CORS with credentials

DB_PATH = "checkpoints/movies.db"

# =====================================
# Helper functions
# =====================================
def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Hash password (NOT secure for production!)"""
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"success": False, "error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

def clean_movie_data(movies):
    """Convert NaN and numpy types to JSON-serializable format"""
    if isinstance(movies, pd.DataFrame):
        movies = movies.to_dict(orient='records')
    
    for movie in movies:
        for key, value in movie.items():
            if pd.isna(value):
                movie[key] = None
            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                movie[key] = str(value)
    return movies

# =====================================
# Authentication Routes
# =====================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not username or not email or not password:
            return jsonify({"success": False, "error": "All fields are required"}), 400
        
        if len(password) < 6:
            return jsonify({"success": False, "error": "Password must be at least 6 characters"}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if username or email already exists
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
        if cursor.fetchone():
            conn.close()
            return jsonify({"success": False, "error": "Username or email already exists"}), 400
        
        # Insert new user
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        
        # Get user data
        cursor.execute("SELECT id, username, email, avatar_url, created_at FROM users WHERE id = ?", (user_id,))
        user = dict(cursor.fetchone())
        conn.close()
        
        # Set session
        session['user_id'] = user['id']
        session['username'] = user['username']
        
        return jsonify({
            "success": True,
            "user": user
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Log in a user"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({"success": False, "error": "Username and password are required"}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Find user by username or email
        password_hash = hash_password(password)
        cursor.execute(
            "SELECT id, username, email, avatar_url, created_at FROM users WHERE (username = ? OR email = ?) AND password_hash = ?",
            (username, username, password_hash)
        )
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({"success": False, "error": "Invalid username or password"}), 401
        
        user = dict(user)
        
        # Set session
        session['user_id'] = user['id']
        session['username'] = user['username']
        
        return jsonify({
            "success": True,
            "user": user
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Log out the current user"""
    session.clear()
    return jsonify({"success": True})

@app.route('/api/auth/me')
def get_current_user():
    """Get current logged-in user"""
    if 'user_id' not in session:
        return jsonify({"success": False, "user": None})
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, avatar_url, created_at FROM users WHERE id = ?",
            (session['user_id'],)
        )
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            session.clear()
            return jsonify({"success": False, "user": None})
        
        return jsonify({
            "success": True,
            "user": dict(user)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =====================================
# Favorites/Watchlist Routes
# =====================================

@app.route('/api/favorites', methods=['GET'])
@login_required
def get_favorites():
    """Get user's favorite movies"""
    try:
        status = request.args.get('status')  # Optional filter by status
        
        conn = get_db()
        cursor = conn.cursor()
        
        if status:
            cursor.execute(
                "SELECT movie_id, status, created_at, updated_at FROM favorites WHERE user_id = ? AND status = ? ORDER BY updated_at DESC",
                (session['user_id'], status)
            )
        else:
            cursor.execute(
                "SELECT movie_id, status, created_at, updated_at FROM favorites WHERE user_id = ? ORDER BY updated_at DESC",
                (session['user_id'],)
            )
        
        favorites = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Get movie details for each favorite
        movie_list = []
        for fav in favorites:
            movie = combined_df[combined_df["id"] == fav['movie_id']]
            if not movie.empty:
                movie_dict = movie.iloc[0].to_dict()
                movie_dict['favorite_status'] = fav['status']
                movie_dict['favorited_at'] = fav['created_at']
                movie_list.append(movie_dict)
        
        return jsonify({
            "success": True,
            "data": clean_movie_data(movie_list)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/favorites/<movie_id>', methods=['POST'])
@login_required
def add_favorite(movie_id):
    """Add movie to favorites"""
    try:
        data = request.get_json()
        status = data.get('status', 'watch_later')
        
        if status not in ['watch_later', 'watching', 'completed', 'dropped']:
            return jsonify({"success": False, "error": "Invalid status"}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if already exists
        cursor.execute(
            "SELECT id, status FROM favorites WHERE user_id = ? AND movie_id = ?",
            (session['user_id'], movie_id)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update status
            cursor.execute(
                "UPDATE favorites SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND movie_id = ?",
                (status, session['user_id'], movie_id)
            )
        else:
            # Insert new
            cursor.execute(
                "INSERT INTO favorites (user_id, movie_id, status) VALUES (?, ?, ?)",
                (session['user_id'], movie_id, status)
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "status": status
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/favorites/<movie_id>', methods=['DELETE'])
@login_required
def remove_favorite(movie_id):
    """Remove movie from favorites"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM favorites WHERE user_id = ? AND movie_id = ?",
            (session['user_id'], movie_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/favorites/<movie_id>/status', methods=['GET'])
@login_required
def get_favorite_status(movie_id):
    """Get favorite status for a movie"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status FROM favorites WHERE user_id = ? AND movie_id = ?",
            (session['user_id'], movie_id)
        )
        result = cursor.fetchone()
        conn.close()
        
        return jsonify({
            "success": True,
            "status": result['status'] if result else None
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =====================================
# Movie API Routes
# =====================================

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "Movie API is running"})

@app.route('/api/movies/top-rated')
def get_top_rated():
    """Get top rated movies - curated list"""
    try:
        top_rated_ids = [
            'tt1375666',  # Inception
            'tt0137523',  # Fight Club
            'tt0133093',  # The Matrix
            'tt0816692',  # Interstellar
            'tt0120815',  # Saving Private Ryan
            'tt0120689',  # The Green Mile
            'tt0317248',  # City of God
            'tt0118799',  # Life Is Beautiful
            'tt0245429',  # Spirited Away
            'tt0253474',  # The Pianist
            'tt0172495',  # Gladiator (2000)
            'tt6751668',  # Parasite
            'tt0407887',  # The Departed
            'tt2582802',  # Whiplash
            'tt0482571',  # The Prestige
            'tt0120586',  # American History X
            'tt9362722',  # Spider-Man: Across The Spider-Verse
            'tt1675434',  # The Intouchables
            'tt0910970',  # WALL·E
            'tt15239678', # Dune: Part Two
        ]
        
        # Get movies in the specified order
        movies = []
        for movie_id in top_rated_ids:
            movie_row = combined_df[combined_df["id"] == movie_id]
            if not movie_row.empty:
                movies.append(movie_row.iloc[0].to_dict())
        
        return jsonify({
            "success": True,
            "data": clean_movie_data(movies)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/movies/genre/<genre>')
def get_movies_by_genre(genre):
    """Get movies by genre"""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        if "genre" not in combined_df.columns:
            return jsonify({"success": False, "error": "Genre column not found"}), 400
            
        genre_df = combined_df[combined_df["genre"].apply(lambda x: genre.lower() in str(x).lower())]
        sort_cols = [c for c in ["rating", "vote_count"] if c in genre_df.columns]
        
        if sort_cols:
            genre_df = genre_df.sort_values(by=sort_cols, ascending=False)
        
        movies = genre_df.head(limit)
        
        return jsonify({
            "success": True,
            "data": clean_movie_data(movies),
            "total": len(genre_df)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/genres')
def get_all_genres():
    """Get curated movies for each genre"""
    try:
        # Curated genre lists with well-known movies (balanced rating + popularity)
        genre_ids = {
            "Action": [
                'tt10366206',  # John Wick: Chapter 4
                'tt9603208',  # Mission: Impossible – The Final Reckoning
                'tt7888964',  # Nobody
                'tt12593682',  # Bullet Train
                'tt7991608',  # Red Notice
                'tt29603959',  # Novocaine
                'tt0356910',  # Mr. & Mrs. Smith
                'tt1684562',  # The Fall Guy
                'tt0266697',  # Kill Bill: Vol. 1
                'tt4919268',  # Bad Boys: Ride or Die
                'tt13314558',  # Day Shift
                'tt6499752',  # Upgrade
                'tt15314262',  # The Beekeeper
                'tt4139588',  # Polar
                'tt8106534',  # 6 Underground
                'tt8385148',  # The Hitman's Wife's Bodyguard
                'tt7737528',  # KATE
                'tt1013743',  # Knight and Day
                'tt4463894',  # Shaft
                'tt6334354',  # The Suicide Squad
            ],
            "Drama": [
                'tt0137523',  # Fight Club
                'tt0816692',  # Interstellar
                'tt0120815',  # Saving Private Ryan
                'tt0114369',  # Se7en
                'tt0120689',  # The Green Mile
                'tt0118799',  # Life Is Beautiful
                'tt0253474',  # The Pianist
                'tt0407887',  # The Departed
                'tt0482571',  # The Prestige
                'tt2582802',  # Whiplash
                'tt0172495',  # Gladiator
                'tt6751668',  # Parasite
                'tt0110912',  # Pulp Fiction
                'tt0317248',  # City of God
                'tt1675434',  # The Intouchables
                'tt0364569',  # Oldboy
                'tt0338013',  # Eternal Sunshine of the Spotless Mind
                'tt0120586',  # American History X
                'tt3315342',  # Logan
                'tt15239678',  # Dune: Part Two
            ],
            "Animation": [
                'tt0245429',  # Spirited Away
                'tt0910970',  # WALL·E
                'tt9362722',  # Spider-Man: Across the Spider-Verse
                'tt4633694',  # Spider-Man: Into the Spider-Verse
                'tt5311514',  # Your Name
                'tt1049413',  # Up
                'tt0119698',  # Princess Mononoke
                'tt2380307',  # Coco
                'tt0114709',  # Toy Story
                'tt0317705',  # The Incredibles
                'tt0382932',  # Ratatouille
                'tt0325980',  # Pirates of the Caribbean: The Curse of the Black Pearl
                'tt2103281',  # Puss in Boots
                'tt5113040',  # The Secret Life of Pets 2
                'tt30017619',  # The Bad Guys 2
                'tt29623480',  # The Wild Robot
                'tt6587046',  # The Boy and the Heron
                'tt10954718',  # Dog Man
                'tt6467266',  # Sing 2
                'tt5220122',  # Hotel Transylvania: Summer Vacation
                'tt3915174',  # Puss in Boots: The Last Wish
            ],
            "Sci-Fi": [
                'tt1375666',  # Inception
                'tt0816692',  # Interstellar
                'tt0133093',  # The Matrix
                'tt0482571',  # The Prestige
                'tt0910970',  # WALL·E
                'tt15239678',  # Dune: Part Two
                'tt0338013',  # Eternal Sunshine of the Spotless Mind
                'tt0434409',  # V for Vendetta
                'tt1392190',  # Mad Max: Fury Road
                'tt3315342',  # Logan
                'tt0468569',  # The Dark Knight
                'tt4633694',  # Spider-Man: Into the Spider-Verse
                'tt9362722',  # Spider-Man: Across the Spider-Verse
                'tt0083658',  # Blade Runner
                'tt0088763',  # Back to the Future
                'tt0076759',  # Star Wars
                'tt0078748',  # Alien
                'tt0245429',  # Spirited Away
                'tt1345836',  # The Dark Knight Rises
                'tt0137523',  # Fight Club
            ],
            "Horror": [
                'tt5052448',  # Get Out
                'tt0365748',  # Shaun of the Dead
                'tt1139797',  # Let the Right One In
                'tt23289160',  # Godzilla Minus One
                'tt0078748',  # Alien
                'tt0081505',  # The Shining
                'tt0087843',  # The Evil Dead II
                'tt0119174',  # The Silence of the Lambs
                'tt0113277',  # Heat
                'tt1345836',  # The Dark Knight Rises
                'tt0407887',  # The Departed
                'tt0317248',  # City of God
                'tt6751668',  # Parasite
                'tt0338013',  # Eternal Sunshine of the Spotless Mind
                'tt0364569',  # Oldboy
                'tt0482571',  # The Prestige
                'tt0172495',  # Gladiator
                'tt0120815',  # Saving Private Ryan
                'tt0114369',  # Se7en
                'tt0137523',  # Fight Club
            ],
            "Comedy": [
                'tt0118799',  # Life Is Beautiful
                'tt1675434',  # The Intouchables
                'tt4633694',  # Spider-Man: Into the Spider-Verse
                'tt0910970',  # WALL·E
                'tt0365748',  # Shaun of the Dead
                'tt0114709',  # Toy Story
                'tt1049413',  # Up
                'tt2380307',  # Coco
                'tt0317705',  # The Incredibles
                'tt0382932',  # Ratatouille
                'tt0088763',  # Back to the Future
                'tt1130884',  # Shrek
                'tt0110912',  # Pulp Fiction
                'tt0245429',  # Spirited Away
                'tt0119698',  # Princess Mononoke
                'tt2948356',  # Zootopia
                'tt0892769',  # How to Train Your Dragon
                'tt5311514',  # Your Name
                'tt29623480',  # The Wild Robot
                'tt9362722',  # Spider-Man: Across the Spider-Verse
            ],
            "Romance": [
                'tt0118799',  # Life Is Beautiful
                'tt0338013',  # Eternal Sunshine of the Spotless Mind
                'tt1675434',  # The Intouchables
                'tt5311514',  # Your Name
                'tt0253474',  # The Pianist
                'tt2380307',  # Coco
                'tt0317705',  # The Incredibles
                'tt0910970',  # WALL·E
                'tt1049413',  # Up
                'tt0245429',  # Spirited Away
                'tt0119698',  # Princess Mononoke
                'tt0088763',  # Back to the Future
                'tt0482571',  # The Prestige
                'tt0364569',  # Oldboy
                'tt0407887',  # The Departed
                'tt0172495',  # Gladiator
                'tt0816692',  # Interstellar
                'tt0120689',  # The Green Mile
                'tt0137523',  # Fight Club
                'tt6751668',  # Parasite
            ],
        }
        
        genre_data = {}
        for genre, movie_ids in genre_ids.items():
            movies = []
            for movie_id in movie_ids[:20]:  # Take first 20
                movie_row = combined_df[combined_df["id"] == movie_id]
                if not movie_row.empty:
                    movies.append(movie_row.iloc[0].to_dict())
            genre_data[genre] = clean_movie_data(movies)
        
        return jsonify({
            "success": True,
            "data": genre_data
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/search')
def search():
    """Search movies with smart search algorithm"""
    try:
        query = request.args.get("query", "").strip()
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 36, type=int)
        
        if not query:
            return jsonify({
                "success": True,
                "data": [],
                "query": query,
                "page": 1,
                "total_pages": 1,
                "total_results": 0
            })
        
        # Perform smart search
        results = smart_search(query, df=combined_df, top_n=1000)
        
        if results is None or results.empty:
            return jsonify({
                "success": True,
                "data": [],
                "query": query,
                "page": 1,
                "total_pages": 1,
                "total_results": 0
            })
        
        # Calculate pagination
        total_results = len(results)
        total_pages = max(1, (total_results + per_page - 1) // per_page)
        
        # Get paginated results
        start = (page - 1) * per_page
        end = start + per_page
        paginated_results = results.iloc[start:end]
        
        return jsonify({
            "success": True,
            "data": clean_movie_data(paginated_results),
            "query": query,
            "page": page,
            "total_pages": total_pages,
            "total_results": total_results
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/movie/<movie_id>')
def get_movie_detail(movie_id):
    """Get detailed information about a specific movie"""
    try:
        movie = combined_df.loc[combined_df["id"] == movie_id].to_dict(orient="records")
        
        if not movie:
            return jsonify({
                "success": False,
                "error": "Movie not found"
            }), 404
        
        movie = movie[0]
        
        # Clean movie data
        for key, value in movie.items():
            if pd.isna(value):
                movie[key] = None
        
        # Get trailer URLs
        trailer_url = None
        tmdb_trailer_url = None
        
        # Check for TMDB trailer URL first (embedded YouTube)
        if "tmdb_trailer_url" in movie and movie["tmdb_trailer_url"]:
            tmdb_trailer_url = movie["tmdb_trailer_url"]
        
        # Get IMDb trailer URL as fallback
        if "trailer_url" in movie and movie["trailer_url"]:
            trailer_url = movie["trailer_url"]
        elif "trailer" in movie and movie["trailer"] and "youtube.com" in str(movie["trailer"]):
            trailer_url = movie["trailer"]
        
        # Find similar movies by genre, prioritizing popular movies
        similar_movies = []
        if "genre" in movie and movie["genre"]:
            # Get all genres from the current movie
            genres = [g.strip().lower() for g in str(movie["genre"]).split(",")]
            
            # Filter movies that share at least one genre
            similar_df = combined_df[
                combined_df["genre"].apply(
                    lambda x: any(g in str(x).lower() for g in genres) if pd.notna(x) else False
                )
            ]
            
            # Exclude current movie
            similar_df = similar_df[similar_df["id"] != movie_id]
            
            # Sort by popularity and vote_count to get well-known movies
            # First by vote_count (minimum threshold for credibility), then by rating
            similar_df = similar_df[similar_df["vote_count"] > 50000]  # Only movies with significant votes
            similar_df = similar_df.sort_values(
                by=["rating", "vote_count"], 
                ascending=[False, False]
            )
            
            similar_movies = clean_movie_data(similar_df.head(12))
        
        return jsonify({
            "success": True,
            "data": {
                "movie": movie,
                "trailer_url": trailer_url,
                "tmdb_trailer_url": tmdb_trailer_url,
                "similar_movies": similar_movies
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =====================================
# Serve React Frontend - Catch-all route (must be LAST)
# =====================================

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors by serving React app for non-API routes"""
    # If it's an API route, return JSON error
    if request.path.startswith('/api/'):
        return jsonify({"error": "API endpoint not found"}), 404
    
    # Otherwise serve index.html for React Router
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except:
        return jsonify({"error": "Frontend build not found. Please run: cd frontend && npm run build"}), 500

@app.route('/')
def serve_root():
    """Serve React app root"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_react(path):
    """Serve React app for all non-API routes"""
    # If requesting a file from assets folder or static resources
    if '.' in path.split('/')[-1]:
        file_path = os.path.join(app.static_folder, path)
        if os.path.isfile(file_path):
            return send_from_directory(app.static_folder, path)
    
    # For all other routes, serve index.html and let React Router handle it
    return send_from_directory(app.static_folder, 'index.html')

# =====================================
# Run server
# =====================================
if __name__ == "__main__":
    # Check if frontend build exists
    if not os.path.exists('frontend/dist'):
        print("\n⚠️  WARNING: Frontend build not found!")
        print("Please run: cd frontend && npm run build\n")
    
    app.run(debug=True, port=8000)
