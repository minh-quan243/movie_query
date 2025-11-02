import { useState, useEffect, createContext, useContext } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext({});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing session on mount
    const checkAuth = async () => {
      try {
        const currentUser = await authService.getCurrentUser();
        setUser(currentUser);
      } catch (error) {
        console.error('Auth check failed:', error);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const signUp = async (email, password, username) => {
    setLoading(true);
    try {
      const newUser = await authService.signUp(email, password, username);
      setUser(newUser);
      return newUser;
    } finally {
      setLoading(false);
    }
  };

  const signIn = async (email, password) => {
    setLoading(true);
    try {
      const loggedInUser = await authService.signIn(email, password);
      setUser(loggedInUser);
      return loggedInUser;
    } finally {
      setLoading(false);
    }
  };

  const signOut = async () => {
    setLoading(true);
    try {
      await authService.signOut();
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const value = {
    user,
    profile: user, // Profile is the same as user in our simple implementation
    loading,
    signUp,
    signIn,
    signOut,
    // Placeholder functions for profile features not yet implemented
    updateProfile: async () => {
      console.warn('Update profile not implemented yet');
    },
    uploadAvatar: async () => {
      console.warn('Upload avatar not implemented yet');
    },
    changePassword: async () => {
      console.warn('Change password not implemented yet');
    },
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

