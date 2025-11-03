import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Navbar from '../components/Navbar';
import MovieCarousel from '../components/MovieCarousel';
import { movieService } from '../services/movieService';
import './HomePage.css';

const HomePage = () => {
  const [featuredMovies, setFeaturedMovies] = useState([]);
  const [genreMovies, setGenreMovies] = useState({});
  const [loading, setLoading] = useState(true);

  const genres = ['Action', 'Drama', 'Animation', 'Sci-Fi', 'Horror', 'Comedy', 'Romance'];

  useEffect(() => {
    const loadMovies = async () => {
      try {
        setLoading(true);

        const featured = await movieService.getTopRatedMovies(20);
        setFeaturedMovies(featured);

        const allGenresData = await movieService.getAllGenres();
        setGenreMovies(allGenresData);
      } catch (error) {
        console.error('Error loading movies:', error);
      } finally {
        setLoading(false);
      }
    };

    loadMovies();
  }, []);

  if (loading) {
    return (
      <div className="home-page">
        <Navbar />
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading movies...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="home-page">
      <Navbar />

      <motion.div
        className="home-content"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        <section className="featured-section">
          <MovieCarousel title="Top Rated Movies" movies={featuredMovies} />
        </section>

        <section className="genres-section">
          {genres.map((genre) => (
            <MovieCarousel
              key={genre}
              title={genre}
              movies={genreMovies[genre] || []}
            />
          ))}
        </section>
      </motion.div>
    </div>
  );
};

export default HomePage;
