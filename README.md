# Movie Query - Full Stack Movie Discovery Platform

A modern full-stack movie discovery application with React frontend and Flask backend, featuring intelligent TF-IDF-based search, user authentication, and personalized watchlists.

## ✨ Features

### Core Features
- 🎬 **Smart Movie Search** - TF-IDF-based intelligent search with NLP processing
- 🔍 **Multi-Type Search** - Search by title, genre, year, cast, director, or plot keywords
- 📊 **Top-Rated Movies** - Discover highly-rated films with advanced filtering
- 🎯 **Genre Browsing** - Browse movies by genre with popularity sorting
- 🎥 **Movie Details** - Comprehensive movie information with trailers and similar recommendations
- 💾 **Extensive Database** - 30+ years of movie data (1995-2025)

### User Features
- 👤 **User Authentication** - Secure registration and login system
- ⭐ **Favorites & Watchlist** - Save movies with custom status (Watch Later, Watching, Completed, Dropped)
- 🎨 **Modern UI** - Beautiful interface with Framer Motion animations
- 📱 **Responsive Design** - Works seamlessly on desktop and mobile devices

## 🛠️ Tech Stack

### Backend
- **Flask 3.1.2** - Python web framework with REST API
- **Flask-CORS** - Cross-origin resource sharing support
- **SQLite** - Lightweight database for movies and users
- **scikit-learn** - TF-IDF vectorization and similarity scoring
- **spaCy** - Advanced NLP text processing
- **NLTK** - Natural language toolkit for text preprocessing
- **Pandas** - Data manipulation and analysis

### Frontend
- **React 19.1.1** - Modern UI library
- **Vite 7.1.7** - Fast build tool and dev server
- **React Router 7.9.5** - Client-side routing
- **Framer Motion 12.23.24** - Smooth animations and transitions
- **React Image Crop** - Avatar upload and cropping

## 📁 Project Structure

```
movie_query/
├── app.py                      # Flask REST API server
├── process.py                  # TF-IDF search engine logic
├── metric.py                   # Search evaluation metrics
├── requirements.txt            # Python dependencies
├── evaluation_queries.json     # Test queries for evaluation
│
├── checkpoints/                # Database and ML models
│   ├── movies.db              # SQLite database (movies, users, favorites)
│   ├── vectorizer.pkl         # TF-IDF vectorizer
│   └── tfidf_matrix.pkl       # Pre-computed TF-IDF matrix
│
├── MovieData/                  # Raw movie data
│   ├── crawler.py             # Data collection script
│   ├── movies_out_*.csv       # Movie data by year (1995-2025)
│   ├── movies_out_*.jsonl     # JSONL format movie data
│   └── tmdb_trailer_urls_backup.csv
│
├── start_server/               # Automated startup scripts
│   ├── start_server.sh        # macOS/Linux startup script
│   ├── start_server.bat       # Windows startup script
│   └── README.md
│
└── frontend/                   # React application
    ├── src/
    │   ├── components/        # Reusable components
    │   │   ├── Navbar.jsx
    │   │   ├── MovieCard.jsx
    │   │   ├── MovieCarousel.jsx
    │   │   ├── AuthModal.jsx
    │   │   ├── CustomDropdown.jsx
    │   │   └── ImageCropModal.jsx
    │   ├── pages/             # Page components
    │   │   ├── LandingPage.jsx
    │   │   ├── HomePage.jsx
    │   │   ├── SearchPage.jsx
    │   │   ├── MovieDetailPage.jsx
    │   │   ├── ProfilePage.jsx
    │   │   └── FavoritesPage.jsx
    │   ├── services/          # API services
    │   │   ├── api.js
    │   │   ├── authService.js
    │   │   └── movieService.js
    │   ├── hooks/             # Custom React hooks
    │   ├── assets/            # Images and static assets
    │   └── utils/             # Utility functions
    ├── package.json
    ├── vite.config.js
    └── index.html
```

## 🚀 Setup Instructions

### Quick Start (Recommended)

The easiest way to start the application is using the automated startup scripts:

**macOS/Linux:**
```bash
cd start_server
./start_server.sh
```

**Windows:**
```cmd
cd start_server
start_server.bat
```

The scripts will automatically:
- ✅ Create Python virtual environment
- ✅ Install all Python dependencies
- ✅ Download spaCy language model (`en_core_web_sm`)
- ✅ Install Node.js dependencies
- ✅ Build the React frontend
- ✅ Start the server at `http://127.0.0.1:8000`

⏱️ **First run:** 5-10 minutes  
⚡ **Subsequent runs:** Instant!

See `start_server/README.md` for detailed information.

---

### Manual Setup

If you prefer manual setup:

#### Backend Setup

1. **Navigate to project root:**
   ```bash
   cd movie_query
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download spaCy model:**
   ```bash
   python -m spacy download en_core_web_sm
   ```

#### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Build the frontend:**
   ```bash
   npm run build
   ```

#### Running the Application

**Production Mode (Recommended):**
```bash
# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or .venv\Scripts\activate on Windows

# Start Flask server (serves both API and React frontend)
python app.py
```

Then open **http://127.0.0.1:8000** in your browser! 🎉

**Development Mode (with Hot Reload):**

Terminal 1 - Backend:
```bash
source .venv/bin/activate
python app.py
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

Access the app at `http://localhost:5173` (frontend dev server)

## 📡 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
  - Body: `{ username, email, password }`
- `POST /api/auth/login` - User login
  - Body: `{ username, password }`
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user session

### Favorites/Watchlist
- `GET /api/favorites?status={status}` - Get user's favorite movies (requires auth)
  - Optional status: `watch_later`, `watching`, `completed`, `dropped`
- `POST /api/favorites/<movie_id>` - Add/update movie in favorites (requires auth)
  - Body: `{ status: "watch_later" | "watching" | "completed" | "dropped" }`
- `DELETE /api/favorites/<movie_id>` - Remove movie from favorites (requires auth)
- `GET /api/favorites/<movie_id>/status` - Get favorite status for a movie (requires auth)

### Movies
- `GET /api/health` - Health check endpoint
- `GET /api/movies/top-rated?limit={limit}` - Get top-rated movies
  - Default limit: 20
- `GET /api/movies/genre/{genre}?limit={limit}` - Get movies by genre
  - Example: `/api/movies/genre/Action?limit=30`
- `GET /api/genres` - Get all available genres with movie counts
- `GET /api/search?query={query}&page={page}&per_page={per_page}` - Search movies
  - Parameters:
    - `query` (required): Search term
    - `page` (optional): Page number (default: 1)
    - `per_page` (optional): Results per page (default: 20)
- `GET /api/movie/{id}` - Get movie details with trailer URLs and similar movies

## 🔍 Features in Detail

### Smart Search Engine

The search system uses advanced NLP and machine learning:

**TF-IDF Vectorization:**
- Converts movie data into numerical vectors
- Pre-computed matrix for fast similarity calculations
- Weighted scoring combining relevance and popularity

**NLP Processing (spaCy + NLTK):**
- Text lemmatization and tokenization
- Stopword removal
- Smart query understanding

**Search Types:**
1. **Title Search** - Direct movie name matching with fuzzy matching
2. **Genre Search** - Filter by single or multiple genres
3. **Year Search** - Find movies from specific years or year ranges
4. **Person Search** - Search by actor, director, or crew names
5. **Content Search** - Semantic search through plot descriptions and keywords

**Similarity Scoring:**
- Combines TF-IDF cosine similarity with movie popularity metrics
- Configurable minimum score threshold
- Smart ranking based on relevance and rating

### User Authentication System
**⚠️ This is only for demonstration purposes and should not be used in production as the implementation is basic and lacks security features.**

**Features:**
- Secure password hashing (SHA-256)
- Session-based authentication
- User profile with avatar support
- Protected routes with authentication decorator

**Note:** Current implementation uses basic SHA-256 hashing for development. For production, implement bcrypt or similar secure hashing.

### Favorites & Watchlist

**Status Types:**
- **Watch Later** - Movies you want to watch
- **Watching** - Currently watching
- **Completed** - Finished watching
- **Dropped** - Stopped watching

**Features:**
- Add/remove movies from watchlist
- Update watching status
- Filter favorites by status
- Persistent storage in SQLite database

### Movie Details

For each movie, get:
- **Basic Info** - Title, year, runtime, rating, vote count
- **People** - Director, cast, writer
- **Media** - Poster images, trailer URLs (IMDb and TMDB)
- **Content** - Plot summary, genres, keywords
- **Similar Movies** - 12 recommendations based on genre and popularity

## 💾 Database Schema

The SQLite database (`checkpoints/movies.db`) contains:

### Movies Table
30+ years of data (1995-2025) with 27+ columns:
- `id` - Unique movie identifier
- `title` - Movie title
- `year` - Release year
- `runtime` - Duration in minutes
- `rating` - Average rating
- `vote_count` - Number of votes
- `genre` - Comma-separated genres
- `director` - Director name(s)
- `cast` - Comma-separated cast
- `writer` - Writer name(s)
- `plot` - Plot summary
- `keywords` - Plot keywords
- `poster_url` - Poster image URL
- `trailer_url` - IMDb trailer URL
- `tmdb_trailer_url` - TMDB embedded trailer URL
- And more...

### Users Table
- `id` - User ID (auto-increment)
- `username` - Unique username
- `email` - Unique email
- `password_hash` - Hashed password
- `avatar_url` - Profile picture URL
- `created_at` - Registration timestamp

### Favorites Table
- `id` - Favorite ID (auto-increment)
- `user_id` - Foreign key to users
- `movie_id` - Movie ID
- `status` - Watch status (watch_later, watching, completed, dropped)
- `created_at` - Added timestamp
- `updated_at` - Last updated timestamp

## 📊 Search Evaluation

Use the evaluation system to measure search quality:

```bash
python metric.py
```

**Metrics:**
- **Precision@10** - Accuracy of top 10 results
- **Average Precision (AP)** - Quality across all results
- **Mean Average Precision (MAP)** - Overall system performance

Evaluation queries are defined in `evaluation_queries.json`.

## ⚙️ Configuration

### Environment Variables

**Backend** (Optional):
Create a `.env` file in the root directory:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
PORT=8000
```

**Frontend**:
Create `frontend/.env`:
```env
VITE_API_URL=http://127.0.0.1:8000
```

**Note:** The application works without environment variables using defaults.

### Frontend Configuration

**Vite Config** (`frontend/vite.config.js`):
- Development server runs on port 5173
- Proxy configured for API requests during development
- Build output goes to `frontend/dist`

**CORS Settings**:
- Configured in `app.py` for development origins
- Update for production deployment

## 🏗️ Building for Production

### Frontend Build
```bash
cd frontend
npm run build
```

Build output will be in `frontend/dist/` and automatically served by Flask.

### Production Deployment Checklist

1. **Update `app.py`:**
   - Set `debug=False`
   - Change `app.secret_key` to a secure random key
   - Update CORS origins to your production domain

2. **Use Production WSGI Server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

3. **Database:**
   - Ensure `checkpoints/movies.db` is accessible
   - Set proper file permissions
   - Consider PostgreSQL for production at scale

4. **Security:**
   - Implement proper password hashing (bcrypt)
   - Use HTTPS in production
   - Set up proper CORS policies
   - Add rate limiting
   - Implement JWT for stateless authentication

5. **Environment Variables:**
   - Use environment-specific configurations
   - Store secrets securely (not in code)

## 🔧 Development Tools

### Frontend Development
```bash
cd frontend
npm run dev      # Development server with hot reload
npm run build    # Production build
npm run preview  # Preview production build
npm run lint     # Run ESLint
```

### Backend Development
```bash
python app.py           # Run Flask development server
python metric.py        # Run search evaluation
python process.py       # Test search engine
```

### Data Management
```bash
cd MovieData
python crawler.py       # Run data crawler (if needed)
```

## 🐛 Troubleshooting

### Common Backend Issues

**1. ModuleNotFoundError**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**2. Database not found**
```
Error: no such table: movies
```
- Ensure `checkpoints/movies.db` exists
- Check file path in `app.py` and `process.py`

**3. spaCy model error**
```
OSError: [E050] Can't find model 'en_core_web_sm'
```
```bash
python -m spacy download en_core_web_sm
```

**4. Port already in use**
```
OSError: [Errno 48] Address already in use
```
- Kill the process: `lsof -ti:8000 | xargs kill -9` (macOS/Linux)
- Or change port in `app.py`: `app.run(debug=True, port=8001)`

### Common Frontend Issues

**1. API connection error**
```
Failed to fetch
```
- Ensure backend is running on port 8000
- Check CORS configuration in `app.py`
- Verify `VITE_API_URL` in `frontend/.env`

**2. Module not found**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**3. Build errors**
```bash
# Clear cache and rebuild
rm -rf frontend/dist
cd frontend
npm run build
```

**4. Port 5173 already in use**
- Kill the process: `lsof -ti:5173 | xargs kill -9` (macOS/Linux)
- Or change port in `frontend/vite.config.js`

### Performance Issues

**Slow search:**
- Ensure TF-IDF models are pre-computed in `checkpoints/`
- Check `vectorizer.pkl` and `tfidf_matrix.pkl` exist
- Consider increasing server resources

**Large memory usage:**
- TF-IDF matrix is loaded into memory
- Consider implementing lazy loading for large datasets
- Use database indexes for frequent queries

## 🎯 Future Enhancements

### Planned Features
- [ ] Advanced filters (runtime, rating range, multiple genres)
- [ ] User reviews and ratings
- [ ] Social features (follow users, share watchlists)
- [ ] Movie recommendations based on watch history
- [ ] Email notifications for new releases
- [ ] Multi-language support
- [ ] Mobile app (React Native)

### Technical Improvements
- [ ] Implement bcrypt for password hashing
- [ ] Add JWT authentication
- [ ] PostgreSQL migration for production
- [ ] Redis caching for frequently accessed data
- [ ] Elasticsearch integration for advanced search
- [ ] API rate limiting
- [ ] Comprehensive test suite
- [ ] Docker containerization
- [ ] CI/CD pipeline

## 📝 Contributing

Contributions are welcome! Here's how:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Test thoroughly**
   - Test all affected endpoints
   - Ensure frontend builds successfully
   - Check for console errors
5. **Commit your changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
6. **Push to your branch**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Code Style
- **Backend:** Follow PEP 8 guidelines
- **Frontend:** Use ESLint configuration provided
- **Commits:** Write clear, descriptive commit messages

## 📄 License

This project is for educational purposes. Movie data is sourced from publicly available datasets.

## 🙏 Credits

- **Movie Data:** TMDB, IMDb, and other public sources
- **Libraries:** React, Flask, scikit-learn, spaCy, and all dependencies
- **Icons & Images:** Various sources

---

**Built with ❤️ using React, Flask, and modern web technologies**
