# Movie Query - Full Stack Application

A full-stack movie search application with React frontend and Flask backend featuring TF-IDF based intelligent search.

## Features

- 🎬 Smart movie search using TF-IDF algorithm
- 🎯 Search by title, genre, year, cast, or director
- 📊 Top-rated movies and genre-based browsing
- 🎨 Modern UI with Framer Motion animations
- 🔍 Detailed movie information with trailers
- 💾 SQLite database with 30+ years of movie data

## Tech Stack

### Backend
- **Flask** - Python web framework
- **SQLite** - Database
- **scikit-learn** - TF-IDF vectorization
- **spaCy** - NLP processing
- **NLTK** - Text preprocessing

### Frontend
- **React** - UI library
- **Vite** - Build tool
- **React Router** - Navigation
- **Framer Motion** - Animations

## Project Structure

```
movie_query/
├── app.py                 # Flask REST API
├── process.py             # TF-IDF search engine
├── metric.py              # Evaluation metrics
├── requirements.txt       # Python dependencies
├── checkpoints/           # Database and TF-IDF models
│   ├── movies.db
│   ├── vectorizer.pkl
│   └── tfidf_matrix.pkl
├── MovieData/             # CSV/JSONL movie data
└── frontend/              # React application
    ├── src/
    │   ├── components/    # React components
    │   ├── pages/         # Page components
    │   ├── services/      # API services
    │   └── hooks/         # Custom hooks
    ├── package.json
    └── vite.config.js
```

## Setup Instructions

### 🚀 Quick Start (Recommended)

The easiest way to get started is using the automated startup scripts:

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
- ✅ Set up Python virtual environment
- ✅ Install all Python dependencies
- ✅ Download spaCy language model
- ✅ Install Node.js dependencies
- ✅ Build the frontend
- ✅ Start the server at `http://127.0.0.1:8000`

First run takes 5-10 minutes. Subsequent runs are instant! ⚡

See `start_server/README.md` for more details.

---

### Manual Setup (Advanced)

If you prefer to set up manually:

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

5. **Run the Flask backend:**
   ```bash
   python app.py
   ```
   Backend will run on `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Run the development server:**
   ```bash
   npm run dev
   ```
   Frontend will run on `http://localhost:3000`

## Running the Application

### Quick Start (Production Mode - Single Server)

```bash
# 1. Build the frontend (only needed once, or when frontend changes)
cd frontend
npm run build
cd ..

# 2. Start Flask server (serves both API and React frontend)
source .venv/bin/activate
python app.py
```

Then open **http://localhost:8000** in your browser! 🎉

### Development Mode (with Hot Reload)

If you want to develop with hot reload:

1. **Start the backend server** (in one terminal):
   ```bash
   python app.py
   ```

2. **Start the frontend development server** (in another terminal):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open your browser:**
   Navigate to `http://localhost:3000`

## API Endpoints

### Movies
- `GET /api/health` - Health check
- `GET /api/movies/top-rated?limit=20` - Get top rated movies
- `GET /api/movies/genre/{genre}?limit=20` - Get movies by genre
- `GET /api/genres` - Get all genres with movies
- `GET /api/search?query={query}&page={page}&per_page={per_page}` - Search movies
- `GET /api/movie/{id}` - Get movie details with similar movies

## Features in Detail

### Smart Search
The search engine uses:
- **TF-IDF vectorization** for content-based matching
- **spaCy NLP** for text processing
- **Query type detection** (title, genre, year, person, content)
- **Weighted scoring** combining similarity and popularity

### Search Types
1. **Title Search** - Direct movie name matching
2. **Genre Search** - Filter by movie genres
3. **Year Search** - Find movies from specific years
4. **Person Search** - Search by actor or director name
5. **Content Search** - Semantic search through plot descriptions

## Database

The SQLite database contains:
- **30+ years** of movie data (1995-2025)
- **27+ columns** including:
  - Basic info (title, year, runtime)
  - People (director, cast, writer)
  - Ratings (rating, vote_count)
  - Media (poster_url, trailer_url)
  - Metadata (genre, keywords, plot)

## Development Notes

### Authentication
- Authentication features are currently **disabled**
- Can be implemented with JWT or session-based auth in the future
- Auth service stubs are in place for future implementation

### Removed Features
- Supabase integration (replaced with Flask REST API)
- User profiles and watchlists (can be re-implemented with backend support)

### Environment Variables

**Backend** (optional):
- No environment variables required

**Frontend** (.env):
```env
VITE_API_URL=http://localhost:8000
```

## Building for Production

### Frontend Build
```bash
cd frontend
npm run build
```
The build output will be in `frontend/dist/`

### Backend Deployment
For production deployment:
1. Set `debug=False` in `app.py`
2. Use a production WSGI server like Gunicorn
3. Configure environment-specific settings

## Troubleshooting

### Backend Issues
- **ModuleNotFoundError**: Install missing packages with pip
- **Database not found**: Ensure `checkpoints/movies.db` exists
- **spaCy model error**: Run `python -m spacy download en_core_web_sm`

### Frontend Issues
- **API connection error**: Ensure backend is running on port 8000
- **Module not found**: Run `npm install` in frontend directory
- **Port already in use**: Change port in `vite.config.js`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational purposes.

## Credits

- Movie data from various sources
- Built with React, Flask, and modern web technologies
