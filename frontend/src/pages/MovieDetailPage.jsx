import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import Navbar from '../components/Navbar';
import { movieService } from '../services/movieService';
import { useAuth } from '../hooks/useAuth';
import './MovieDetailPage.css';

const MovieDetailPage = () => {
  const { id } = useParams();
  const { user } = useAuth();

  const [movie, setMovie] = useState(null);
  const [loading, setLoading] = useState(true);
  const [similarMovies, setSimilarMovies] = useState([]);
  const [trailerUrl, setTrailerUrl] = useState(null);
  const [tmdbTrailerUrl, setTmdbTrailerUrl] = useState(null);
  const [watchlistStatus, setWatchlistStatus] = useState(null);

  useEffect(() => {
    const loadMovieData = async () => {
      try {
        setLoading(true);
        const movieData = await movieService.getMovieById(id);
        
        if (movieData && movieData.movie) {
          setMovie(movieData.movie);
          setTrailerUrl(movieData.trailer_url);
          setTmdbTrailerUrl(movieData.tmdb_trailer_url);
          setSimilarMovies(movieData.similar_movies || []);
        }

        // Load watchlist status if user is logged in
        if (user) {
          try {
            const status = await movieService.getFavoriteStatus(id);
            setWatchlistStatus(status);
          } catch (error) {
            console.error('Error loading watchlist status:', error);
          }
        }
      } catch (error) {
        console.error('Error loading movie:', error);
      } finally {
        setLoading(false);
      }
    };

    loadMovieData();
  }, [id, user]);

  const handleWatchlistUpdate = async (status) => {
    if (!user) {
      alert('Please sign in to add movies to your watchlist');
      return;
    }

    try {
      if (watchlistStatus === status) {
        // Remove from watchlist
        await movieService.removeFromFavorites(id);
        setWatchlistStatus(null);
      } else {
        // Add or update watchlist status
        await movieService.addToFavorites(id, status);
        setWatchlistStatus(status);
      }
    } catch (error) {
      console.error('Error updating watchlist:', error);
      alert('Failed to update watchlist. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="movie-detail-page">
        <Navbar />
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading movie details...</p>
        </div>
      </div>
    );
  }

  if (!movie) {
    return (
      <div className="movie-detail-page">
        <Navbar />
        <div className="error-container">
          <p>Movie not found</p>
        </div>
      </div>
    );
  }

  const getPosterUrl = (url) => {
    if (!url) return 'https://via.placeholder.com/300x450?text=No+Poster';
    if (url.includes('_V1_')) {
      return url.replace('_V1_', '_V1_UX500_');
    }
    return url;
  };

  const getBackdropUrl = (url) => {
    if (!url) return null;
    if (url.includes('_V1_')) {
      return url.replace('_V1_', '_V1_UX1000_');
    }
    return url;
  };

  // Parse genres from comma-separated string
  const genres = movie.genre 
    ? movie.genre.replace(/[\[\]"]/g, '').split(',').map(g => g.trim()).filter(g => g)
    : [];

  // Parse cast from comma-separated string and clean it
  const castMembers = movie.cast 
    ? movie.cast.replace(/[\[\]"]/g, '').split(',').map(c => c.trim()).filter(c => c)
    : [];

  // Helper function to clean field values (remove [], "")
  const cleanField = (value) => {
    if (!value) return null;
    const cleaned = String(value).replace(/[\[\]"]/g, '').trim();
    return cleaned || null;
  };

  // Clean director
  const director = cleanField(movie.director);

  // Clean language
  const language = cleanField(movie.language);

  // Clean country
  const country = cleanField(movie.production_country);

  // Clean production companies
  const productionCompanies = cleanField(movie.production_companies);

  const posterUrl = getPosterUrl(movie.poster_url);
  const backdropUrl = getBackdropUrl(movie.poster_url);

  return (
    <div className="movie-detail-page">
      <Navbar />

      {backdropUrl && (
        <div className="backdrop-container">
          <img src={backdropUrl} alt="" className="backdrop-image" />
          <div className="backdrop-overlay"></div>
        </div>
      )}

      <motion.div
        className="movie-detail-content"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="movie-header">
          <div className="poster-container">
            <img src={posterUrl} alt={movie.title} className="movie-poster" />
          </div>

          <div className="movie-info">
            <h1 className="movie-title">{movie.title}</h1>
            {movie.original_title && movie.original_title !== movie.title && (
              <p className="original-title">{movie.original_title}</p>
            )}

            <div className="movie-meta">
              {movie.year && <span className="meta-item">{movie.year}</span>}
              {movie.runtime && <span className="meta-item">{movie.runtime} min</span>}
              {movie.mprating && <span className="meta-badge">{movie.mprating}</span>}
            </div>

            {movie.rating && (
              <div className="rating-section">
                <span className="rating-star">★</span>
                <span className="rating-value">{parseFloat(movie.rating).toFixed(1)}</span>
                {movie.vote_count && (
                  <span className="rating-votes">({movie.vote_count.toLocaleString()} votes)</span>
                )}
              </div>
            )}

            <div className="watchlist-section">
              <label>Add to Watchlist:</label>
              <div className="watchlist-buttons">
                <button
                  className={`watchlist-btn ${watchlistStatus === 'watch_later' ? 'active' : ''}`}
                  onClick={() => handleWatchlistUpdate('watch_later')}
                  disabled={!user}
                >
                  Watch Later
                </button>
                <button
                  className={`watchlist-btn ${watchlistStatus === 'watching' ? 'active' : ''}`}
                  onClick={() => handleWatchlistUpdate('watching')}
                  disabled={!user}
                >
                  Watching
                </button>
                <button
                  className={`watchlist-btn ${watchlistStatus === 'completed' ? 'active' : ''}`}
                  onClick={() => handleWatchlistUpdate('completed')}
                  disabled={!user}
                >
                  Completed
                </button>
                <button
                  className={`watchlist-btn ${watchlistStatus === 'dropped' ? 'active' : ''}`}
                  onClick={() => handleWatchlistUpdate('dropped')}
                  disabled={!user}
                >
                  Dropped
                </button>
              </div>
              {!user && <p className="watchlist-note" style={{ marginTop: '1rem' }}>Sign in to add to your watchlist</p>}
            </div>

            {movie.plot && (
              <div className="plot-section">
                <h3>Plot</h3>
                <p>{movie.plot}</p>
              </div>
            )}

            <div className="movie-details-grid">
              {director && (
                <div className="detail-item">
                  <strong>Director:</strong>
                  <span>{director}</span>
                </div>
              )}

              {castMembers.length > 0 && (
                <div className="detail-item">
                  <strong>Cast:</strong>
                  <span>{castMembers.slice(0, 6).join(', ')}</span>
                </div>
              )}

              {genres.length > 0 && (
                <div className="detail-item">
                  <strong>Genres:</strong>
                  <div className="genres-list">
                    {genres.map((genre, index) => (
                      <span key={index} className="genre-tag">{genre}</span>
                    ))}
                  </div>
                </div>
              )}

              {language && (
                <div className="detail-item">
                  <strong>Language:</strong>
                  <span>{language}</span>
                </div>
              )}

              {country && (
                <div className="detail-item">
                  <strong>Country:</strong>
                  <span>{country}</span>
                </div>
              )}

              {productionCompanies && (
                <div className="detail-item">
                  <strong>Production:</strong>
                  <span>{productionCompanies}</span>
                </div>
              )}

              {movie.awards && movie.awards.trim() && (
                <div className="detail-item">
                  <strong>Awards:</strong>
                  <span>{movie.awards}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {(tmdbTrailerUrl || trailerUrl) && (
          <div className="trailer-section">
            <h2>Trailer</h2>
            {tmdbTrailerUrl ? (
              <div className="trailer-container">
                <iframe
                  src={tmdbTrailerUrl}
                  title="Movie Trailer"
                  frameBorder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                ></iframe>
              </div>
            ) : (
              <div className="trailer-link-container">
                <a 
                  href={trailerUrl} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="trailer-button"
                >
                  Watch Trailer on IMDb
                </a>
              </div>
            )}
          </div>
        )}

        {similarMovies.length > 0 && (
          <div className="similar-movies-section">
            <h3>Similar Movies</h3>
            <div className="similar-movies-list">
              {similarMovies.slice(0, 20).map((similarMovie) => {
                const similarPosterUrl = getPosterUrl(similarMovie.poster_url)?.replace('_V1_UX500_', '_V1_UX160_');
                return (
                  <a
                    key={similarMovie.id}
                    href={`/movie/${similarMovie.id}`}
                    className="similar-movie-item"
                    onClick={(e) => {
                      e.preventDefault();
                      window.location.href = `/movie/${similarMovie.id}`;
                    }}
                  >
                    <img src={similarPosterUrl} alt={similarMovie.title} />
                    <p>{similarMovie.title}</p>
                  </a>
                );
              })}
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
};

export default MovieDetailPage;
