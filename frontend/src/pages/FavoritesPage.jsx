import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../hooks/useAuth';
import { movieService } from '../services/movieService';
import Navbar from '../components/Navbar';
import MovieCard from '../components/MovieCard';
import './FavoritesPage.css';

const FavoritesPage = () => {
  const { user } = useAuth();
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState(null);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }

    const loadFavorites = async () => {
      try {
        setLoading(true);
        const data = await movieService.getFavorites(filter);
        setFavorites(data);
      } catch (error) {
        console.error('Error loading favorites:', error);
      } finally {
        setLoading(false);
      }
    };

    loadFavorites();
  }, [user, filter]);

  if (!user) {
    return (
      <div className="favorites-page">
        <Navbar />
        <div className="favorites-content">
          <motion.div
            className="not-signed-in"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h1>My Watchlist</h1>
            <p>Please sign in to view your watchlist</p>
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <div className="favorites-page">
      <Navbar />
      
      <div className="favorites-content">
        <motion.div
          className="favorites-header"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1>My Watchlist</h1>
          
          <div className="filter-buttons">
            <button
              className={`filter-btn ${filter === null ? 'active' : ''}`}
              onClick={() => setFilter(null)}
            >
              All ({favorites.length})
            </button>
            <button
              className={`filter-btn ${filter === 'watch_later' ? 'active' : ''}`}
              onClick={() => setFilter('watch_later')}
            >
              Watch Later
            </button>
            <button
              className={`filter-btn ${filter === 'watching' ? 'active' : ''}`}
              onClick={() => setFilter('watching')}
            >
              Watching
            </button>
            <button
              className={`filter-btn ${filter === 'completed' ? 'active' : ''}`}
              onClick={() => setFilter('completed')}
            >
              Completed
            </button>
            <button
              className={`filter-btn ${filter === 'dropped' ? 'active' : ''}`}
              onClick={() => setFilter('dropped')}
            >
              Dropped
            </button>
          </div>
        </motion.div>

        {loading ? (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>Loading your watchlist...</p>
          </div>
        ) : favorites.length > 0 ? (
          <motion.div
            className="favorites-grid"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            {favorites.map((movie) => (
              <MovieCard key={movie.id} movie={movie} />
            ))}
          </motion.div>
        ) : (
          <div className="no-favorites">
            <p>No movies in your watchlist yet. Start adding some!</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FavoritesPage;
