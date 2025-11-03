import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import './MovieCard.css';

const MovieCard = ({ movie, checkbox }) => {
  const navigate = useNavigate();

  // Handle poster URL - replace _V1_ with _V1_UX200_ for lower resolution
  const posterUrl = movie.poster_url || movie.poster_path || movie.poster;
  const optimizedPosterUrl = posterUrl
    ? posterUrl.replace('_V1_', '_V1_UX200_')
    : 'https://via.placeholder.com/300x450?text=No+Poster';

  // Parse genres from comma-separated string to array and clean up
  let genres = [];
  if (movie.genres) {
    // If it's already an array
    if (Array.isArray(movie.genres)) {
      genres = movie.genres;
    } else if (typeof movie.genres === 'string') {
      genres = movie.genres.split(',').map(g => g.trim()).filter(g => g && g !== '[]' && g !== '""');
    }
  } else if (movie.genre) {
    // Parse from genre field (comma-separated string)
    if (typeof movie.genre === 'string') {
      genres = movie.genre
        .replace(/[\[\]"]/g, '') // Remove brackets and quotes
        .split(',')
        .map(g => g.trim())
        .filter(g => g && g.length > 0); // Remove empty strings
    }
  }

  const isSelectionMode = checkbox?.selectionMode || false;

  return (
    <motion.div
      className={`movie-card ${isSelectionMode ? 'selection-mode' : ''}`}
      whileHover={isSelectionMode ? {} : { scale: 1.05, y: -10 }}
      transition={{ duration: 0.3 }}
      onClick={() => navigate(`/movie/${movie.id}`)}
    >
      {checkbox && (
        <div
          className={`movie-checkbox ${checkbox.show ? 'show' : ''} ${checkbox.selected ? 'selected' : ''}`}
          onClick={(e) => {
            e.stopPropagation();
            checkbox.onToggle();
          }}
        >
          <input
            type="checkbox"
            checked={checkbox.selected}
            onChange={() => {}}
          />
        </div>
      )}
      <div className="movie-card-image-wrapper">
        <img
          src={optimizedPosterUrl}
          alt={movie.title}
          className="movie-card-image"
          loading="lazy"
        />
        <div className="movie-card-overlay">
          <div className="movie-card-rating">
            <span className="star">★</span>
            {movie.rating ? movie.rating.toFixed(1) : 'N/A'}
          </div>
        </div>
      </div>

      <div className="movie-card-info">
        <h3 className="movie-card-title">{movie.title}</h3>
        <div className="movie-card-meta">
          <span className="movie-card-year">{movie.year}</span>
          {movie.runtime && (
            <>
              <span className="dot">•</span>
              <span className="movie-card-runtime">{movie.runtime} min</span>
            </>
          )}
        </div>
        {genres && genres.length > 0 && (
          <div className="movie-card-genres">
            {genres.slice(0, 3).map((genre, index) => (
              <span key={index} className="genre-tag">{genre}</span>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default MovieCard;
