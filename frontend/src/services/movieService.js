import api from './api';

export const movieService = {
  async getTopRatedMovies(limit = 20) {
    const response = await api.getTopRatedMovies(limit);
    return response.data;
  },

  async getMoviesByGenre(genre, limit = 20) {
    const response = await api.getMoviesByGenre(genre, limit);
    return response.data;
  },

  async getAllGenres() {
    const response = await api.getAllGenres();
    return response.data;
  },

  async searchMovies(query, filters = {}) {
    const response = await api.searchMovies(query, 1, 1000); // Get all results for filtering
    let movies = response.data;

    // Apply client-side filtering for genres
    if (filters.genres && filters.genres.length > 0) {
      movies = movies.filter(movie => {
        if (!movie.genre) return false;
        const movieGenres = movie.genre.toLowerCase();
        return filters.genres.some(genre => 
          movieGenres.includes(genre.toLowerCase())
        );
      });
    }

    // Apply client-side filtering for year range
    if (filters.yearRange && filters.yearRange.length === 2) {
      const [minYear, maxYear] = filters.yearRange;
      movies = movies.filter(movie => {
        const year = parseInt(movie.year);
        return year >= minYear && year <= maxYear;
      });
    }

    return movies;
  },

  async getMovieById(id) {
    const response = await api.getMovieById(id);
    return response.data;
  },

  // Favorites/Watchlist functions
  async getFavorites(status = null) {
    const url = status ? `/api/favorites?status=${status}` : '/api/favorites';
    const response = await fetch(url, {
      credentials: 'include',
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Failed to get favorites');
    }
    return data.data;
  },

  async addToFavorites(movieId, status = 'watch_later') {
    const response = await fetch(`/api/favorites/${movieId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ status }),
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Failed to add to favorites');
    }
    return data.status;
  },

  async removeFromFavorites(movieId) {
    const response = await fetch(`/api/favorites/${movieId}`, {
      method: 'DELETE',
      credentials: 'include',
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Failed to remove from favorites');
    }
    return true;
  },

  async getFavoriteStatus(movieId) {
    const response = await fetch(`/api/favorites/${movieId}/status`, {
      credentials: 'include',
    });
    const data = await response.json();
    if (!data.success) {
      return null;
    }
    return data.status;
  },

  // Note: Watchlist and comments features are removed
  // They were Supabase-specific and would need backend implementation
  // For now, these features are disabled
};

