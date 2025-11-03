// API base URL - will use Vite proxy in development
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

/**
 * Generic API request handler
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'An error occurred');
    }

    return data;
  } catch (error) {
    console.error('API Request Error:', error);
    throw error;
  }
}

/**
 * API client for movie-related endpoints
 */
export const api = {
  /**
   * Health check
   */
  async healthCheck() {
    return apiRequest('/health');
  },

  /**
   * Get top rated movies
   */
  async getTopRatedMovies(limit = 20) {
    return apiRequest(`/movies/top-rated?limit=${limit}`);
  },

  /**
   * Get movies by genre
   */
  async getMoviesByGenre(genre, limit = 20) {
    return apiRequest(`/movies/genre/${encodeURIComponent(genre)}?limit=${limit}`);
  },

  /**
   * Get all genres with movies
   */
  async getAllGenres() {
    return apiRequest('/genres');
  },

  /**
   * Search movies
   */
  async searchMovies(query, page = 1, perPage = 36) {
    const params = new URLSearchParams({
      query,
      page: page.toString(),
      per_page: perPage.toString(),
    });
    return apiRequest(`/search?${params}`);
  },

  /**
   * Get movie by ID
   */
  async getMovieById(id) {
    return apiRequest(`/movie/${encodeURIComponent(id)}`);
  },
};

export default api;
