import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import Navbar from '../components/Navbar';
import MovieCard from '../components/MovieCard';
import { movieService } from '../services/movieService';
import './SearchPage.css';

const SearchPage = () => {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';

  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedGenres, setSelectedGenres] = useState([]);
  const [yearRange, setYearRange] = useState([1995, new Date().getFullYear()]);

  const genres = ['Action', 'Drama', 'Animation', 'Sci-Fi', 'Horror', 'Comedy', 'Romance', 'Thriller', 'Fantasy', 'Mystery'];

  useEffect(() => {
    const searchMovies = async () => {
      if (!query) return;

      try {
        setLoading(true);
        const results = await movieService.searchMovies(query, {
          genres: selectedGenres,
          yearRange: yearRange,
        });
        setMovies(results);
      } catch (error) {
        console.error('Error searching movies:', error);
      } finally {
        setLoading(false);
      }
    };

    searchMovies();
  }, [query, selectedGenres, yearRange]);

  const toggleGenre = (genre) => {
    setSelectedGenres((prev) =>
      prev.includes(genre)
        ? prev.filter((g) => g !== genre)
        : [...prev, genre]
    );
  };

  return (
    <div className="search-page">
      <Navbar />

      <div className="search-content">
        <motion.div
          className="search-header"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1>Search Results for "{query}"</h1>
          <p className="results-count">
            {movies.length} {movies.length === 1 ? 'movie' : 'movies'} found
          </p>
        </motion.div>

        <div className="search-layout">
          <aside className="filters-sidebar">
            <div className="filter-section">
              <h3 className="filter-title">Genres</h3>
              <div className="genre-filters">
                {genres.map((genre) => (
                  <button
                    key={genre}
                    className={`genre-chip ${selectedGenres.includes(genre) ? 'active' : ''}`}
                    onClick={() => toggleGenre(genre)}
                  >
                    {genre}
                  </button>
                ))}
              </div>
            </div>

            <div className="filter-section">
              <h3 className="filter-title">Year Range</h3>
              <div className="year-slider">
                <div className="year-inputs">
                  <input
                    type="number"
                    min="1995"
                    max={new Date().getFullYear()}
                    value={yearRange[0]}
                    onChange={(e) => setYearRange([parseInt(e.target.value), yearRange[1]])}
                    className="year-input"
                  />
                  <span>to</span>
                  <input
                    type="number"
                    min="1995"
                    max={new Date().getFullYear()}
                    value={yearRange[1]}
                    onChange={(e) => setYearRange([yearRange[0], parseInt(e.target.value)])}
                    className="year-input"
                  />
                </div>
              </div>
            </div>

            {(selectedGenres.length > 0 || yearRange[0] !== 1995 || yearRange[1] !== new Date().getFullYear()) && (
              <button
                className="clear-filters-button"
                onClick={() => {
                  setSelectedGenres([]);
                  setYearRange([1995, new Date().getFullYear()]);
                }}
              >
                Clear Filters
              </button>
            )}
          </aside>

          <main className="search-results">
            {loading ? (
              <div className="loading-container">
                <div className="loading-spinner"></div>
                <p>Searching...</p>
              </div>
            ) : movies.length > 0 ? (
              <motion.div
                className="movies-grid"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5 }}
              >
                {movies.map((movie) => (
                  <MovieCard key={movie.id} movie={movie} />
                ))}
              </motion.div>
            ) : (
              <div className="no-results">
                <p>No movies found. Try adjusting your filters or search query.</p>
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
};

export default SearchPage;
