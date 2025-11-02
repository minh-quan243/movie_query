// Auth service using Flask backend with session-based authentication
// WARNING: For educational purposes only - NOT production-ready!

export const authService = {
  async signUp(email, password, username) {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username, email, password }),
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Registration failed');
    }
    return data.user;
  },

  async signIn(email, password) {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username: email, password }),
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Login failed');
    }
    return data.user;
  },

  async signOut() {
    const response = await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'include',
    });
    const data = await response.json();
    return data;
  },

  async getCurrentUser() {
    try {
      const response = await fetch('/api/auth/me', {
        credentials: 'include',
      });
      const data = await response.json();
      return data.success ? data.user : null;
    } catch (error) {
      console.error('Error getting current user:', error);
      return null;
    }
  },

  async getProfile(userId) {
    // Not implemented - returns current user instead
    return this.getCurrentUser();
  },

  async updateProfile(userId, updates) {
    // TODO: Implement backend authentication
    throw new Error('Authentication feature is currently disabled');
  },

  async uploadAvatar(userId, file) {
    // TODO: Implement backend authentication
    throw new Error('Authentication feature is currently disabled');
  },

  async updatePassword(newPassword) {
    // TODO: Implement backend authentication
    throw new Error('Authentication feature is currently disabled');
  },
};

