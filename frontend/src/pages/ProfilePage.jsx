import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Navbar from '../components/Navbar';
import MovieCard from '../components/MovieCard';
import CustomDropdown from '../components/CustomDropdown';
import ImageCropModal from '../components/ImageCropModal';
import { useAuth } from '../hooks/useAuth';
import { movieService } from '../services/movieService';
import './ProfilePage.css';

const ProfilePage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, profile, signOut, updateProfile, uploadAvatar, changePassword } = useAuth();
  const fileInputRef = useRef(null);

  const [watchlistFilter, setWatchlistFilter] = useState('all');
  const [watchlistMovies, setWatchlistMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editUsername, setEditUsername] = useState('');
  const [editEmail, setEditEmail] = useState('');
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [cropModalOpen, setCropModalOpen] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedMovies, setSelectedMovies] = useState(new Set());
  const [hoveredMovie, setHoveredMovie] = useState(null);
  const moviesPerPage = 8;

  useEffect(() => {
    if (!user) {
      navigate('/home');
      return;
    }

    // Convert id from URL params to number for comparison
    const profileId = parseInt(id, 10);
    if (user.id !== profileId) {
      navigate('/home');
      return;
    }

    const loadWatchlist = async () => {
      try {
        setLoading(true);
        const status = watchlistFilter === 'all' ? null : watchlistFilter;
        const data = await movieService.getFavorites(status);
        // Transform data to match expected structure
        const transformedData = data.map(movie => ({
          id: movie.id,
          movie_id: movie.id,
          status: movie.favorite_status,
          movies: movie
        }));
        setWatchlistMovies(transformedData);
      } catch (error) {
        console.error('Error loading watchlist:', error);
        setWatchlistMovies([]);
      } finally {
        setLoading(false);
      }
    };

    loadWatchlist();
  }, [user, id, watchlistFilter, navigate]);

  useEffect(() => {
    if (profile) {
      setEditUsername(profile.username || '');
      setEditEmail(profile.email || '');
    }
  }, [profile]);

  const handleSignOut = async () => {
    try {
      await signOut();
      navigate('/landing');
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    try {
      await updateProfile(user.id, {
        username: editUsername,
        email: editEmail,
      });
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating profile:', error);
      alert('Failed to update profile');
    }
  };

  const handleAvatarClick = () => {
    fileInputRef.current?.click();
  };

  const handleAvatarUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      alert('File size must be less than 5MB');
      e.target.value = '';
      return;
    }

    if (!file.type.startsWith('image/')) {
      alert('Please upload an image file');
      e.target.value = '';
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      setSelectedImage(reader.result);
      setCropModalOpen(true);
    };
    reader.readAsDataURL(file);
    e.target.value = '';
  };

  const handleCropComplete = async (croppedFile) => {
    try {
      setAvatarUploading(true);
      setCropModalOpen(false);
      await uploadAvatar(user.id, croppedFile);
      window.location.reload();
    } catch (error) {
      console.error('Error uploading avatar:', error);
      alert('Failed to upload avatar');
    } finally {
      setAvatarUploading(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPasswordError('');

    if (newPassword.length < 6) {
      setPasswordError('Password must be at least 6 characters');
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError('Passwords do not match');
      return;
    }

    try {
      await changePassword(newPassword);
      setIsChangingPassword(false);
      setNewPassword('');
      setConfirmPassword('');
      alert('Password changed successfully');
    } catch (error) {
      console.error('Error changing password:', error);
      setPasswordError(error.message || 'Failed to change password');
    }
  };

  const handleMovieSelect = (movieId) => {
    setSelectedMovies((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(movieId)) {
        newSet.delete(movieId);
      } else {
        newSet.add(movieId);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    const currentPageMovies = currentMovies;
    const allSelected = currentPageMovies.every(item => selectedMovies.has(item.movie_id));

    setSelectedMovies((prev) => {
      const newSet = new Set(prev);
      currentPageMovies.forEach(item => {
        if (allSelected) {
          newSet.delete(item.movie_id);
        } else {
          newSet.add(item.movie_id);
        }
      });
      return newSet;
    });
  };

  const handleDeleteSelected = async () => {
    if (selectedMovies.size === 0) return;

    if (!confirm(`Delete ${selectedMovies.size} movie(s) from your watchlist?`)) {
      return;
    }

    try {
      await Promise.all(
        Array.from(selectedMovies).map(movieId => {
          return movieService.removeFromFavorites(movieId);
        })
      );

      setWatchlistMovies(prev => prev.filter(item => !selectedMovies.has(item.movie_id)));
      setSelectedMovies(new Set());

      if (watchlistMovies.length - selectedMovies.size <= (currentPage - 1) * moviesPerPage && currentPage > 1) {
        setCurrentPage(currentPage - 1);
      }
    } catch (error) {
      console.error('Error deleting movies:', error);
      alert('Failed to delete some movies');
    }
  };

  const filterOptions = [
    { value: 'all', label: 'All' },
    { value: 'watch_later', label: 'Watch Later' },
    { value: 'watching', label: 'Watching' },
    { value: 'completed', label: 'Completed' },
    { value: 'dropped', label: 'Dropped' }
  ];

  const totalPages = Math.ceil(watchlistMovies.length / moviesPerPage);
  const startIndex = (currentPage - 1) * moviesPerPage;
  const endIndex = startIndex + moviesPerPage;
  const currentMovies = watchlistMovies.slice(startIndex, endIndex);

  if (!user) {
    return (
      <div className="profile-page">
        <Navbar />
        <div className="error-container">
          <p>Please sign in to view your profile</p>
        </div>
      </div>
    );
  }

  return (
    <div className="profile-page">
      <Navbar />

      <ImageCropModal
        isOpen={cropModalOpen}
        onClose={() => {
          setCropModalOpen(false);
          setSelectedImage(null);
        }}
        imageSrc={selectedImage}
        onCropComplete={handleCropComplete}
      />

      <motion.div
        className="profile-content"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="profile-header">
          <div className="avatar-container">
            <div className="profile-avatar-large">
              {profile?.avatar_url ? (
                <img src={profile.avatar_url} alt="Profile" />
              ) : (
                <span>{profile?.username?.[0]?.toUpperCase() || 'U'}</span>
              )}
            </div>
            <button
              className="avatar-edit-button"
              onClick={handleAvatarClick}
              disabled={avatarUploading}
            >
              {avatarUploading ? 'Uploading...' : 'Edit'}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleAvatarUpload}
              style={{ display: 'none' }}
            />
          </div>

          <div className="profile-info">
            <h1>{profile?.username || 'User'}</h1>
            <p className="profile-email">{profile?.email || user.email}</p>
          </div>

          <button className="signout-button" onClick={handleSignOut}>
            Sign Out
          </button>
        </div>

        <div className="profile-sections">
          <section className="account-section">
            <h2>Account Settings</h2>

            {isChangingPassword ? (
              <form onSubmit={handleChangePassword} className="edit-form">
                <h3>Change Password</h3>

                {passwordError && <div className="error-message">{passwordError}</div>}

                <div className="form-group">
                  <label>New Password</label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter new password"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Confirm Password</label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm new password"
                    required
                  />
                </div>

                <div className="form-actions">
                  <button type="submit" className="save-button">
                    Update Password
                  </button>
                  <button
                    type="button"
                    className="cancel-button"
                    onClick={() => {
                      setIsChangingPassword(false);
                      setNewPassword('');
                      setConfirmPassword('');
                      setPasswordError('');
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : isEditing ? (
              <form onSubmit={handleUpdateProfile} className="edit-form">
                <div className="form-group">
                  <label>Username</label>
                  <input
                    type="text"
                    value={editUsername}
                    onChange={(e) => setEditUsername(e.target.value)}
                    placeholder="Enter username"
                  />
                </div>

                <div className="form-group">
                  <label>Email</label>
                  <input
                    type="email"
                    value={editEmail}
                    onChange={(e) => setEditEmail(e.target.value)}
                    placeholder="Enter email"
                  />
                </div>

                <div className="form-actions">
                  <button type="submit" className="save-button">
                    Save Changes
                  </button>
                  <button
                    type="button"
                    className="cancel-button"
                    onClick={() => setIsEditing(false)}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <div className="account-info">
                <div className="info-item">
                  <strong>Username:</strong>
                  <span>{profile?.username || 'Not set'}</span>
                </div>
                <div className="info-item">
                  <strong>Email:</strong>
                  <span>{profile?.email || user.email}</span>
                </div>
                <div className="button-group">
                  <button className="edit-button" onClick={() => setIsEditing(true)}>
                    Edit Profile
                  </button>
                  <button className="password-button" onClick={() => setIsChangingPassword(true)}>
                    Change Password
                  </button>
                </div>
              </div>
            )}
          </section>

          <section className="watchlist-section">
            <div className="watchlist-header">
              <h2>My Watchlist</h2>
              <div className="watchlist-controls">
                <CustomDropdown
                  value={watchlistFilter}
                  onChange={(value) => {
                    setWatchlistFilter(value);
                    setCurrentPage(1);
                    setSelectedMovies(new Set());
                  }}
                  options={filterOptions}
                />
                {selectedMovies.size > 0 && (
                  <div className="bulk-actions">
                    <button className="select-all-button" onClick={handleSelectAll}>
                      {currentMovies.every(item => selectedMovies.has(item.movie_id)) ? 'Deselect All' : 'Select All'}
                    </button>
                    <button className="delete-button" onClick={handleDeleteSelected}>
                      Delete ({selectedMovies.size})
                    </button>
                  </div>
                )}
              </div>
            </div>

            {loading ? (
              <div className="loading-container">
                <div className="loading-spinner"></div>
                <p>Loading watchlist...</p>
              </div>
            ) : watchlistMovies.length > 0 ? (
              <>
                <div className="watchlist-grid">
                  {currentMovies.map((item) => {
                    const isSelected = selectedMovies.has(item.movie_id);
                    const isSelectionMode = selectedMovies.size > 0;
                    const showCheckbox = hoveredMovie === item.movie_id || isSelectionMode;

                    return (
                      <div
                        key={item.movie_id}
                        onMouseEnter={() => {
                          if (!isSelectionMode) {
                            setHoveredMovie(item.movie_id);
                          }
                        }}
                        onMouseLeave={() => {
                          if (!isSelectionMode && !isSelected) {
                            setHoveredMovie(null);
                          }
                        }}
                      >
                        <MovieCard
                          movie={item.movies}
                          checkbox={{
                            show: showCheckbox,
                            selected: isSelected,
                            selectionMode: isSelectionMode,
                            onToggle: () => handleMovieSelect(item.movie_id)
                          }}
                        />
                      </div>
                    );
                  })}
                </div>
                {totalPages > 1 && (
                  <div className="pagination">
                    <button
                      className="pagination-button"
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                    >
                      Previous
                    </button>
                    <div className="pagination-info">
                      Page {currentPage} of {totalPages}
                    </div>
                    <button
                      className="pagination-button"
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
            ) : (
              <div className="empty-watchlist">
                <p>No movies in your watchlist yet</p>
                <button className="browse-button" onClick={() => navigate('/home')}>
                  Browse Movies
                </button>
              </div>
            )}
          </section>
        </div>
      </motion.div>
    </div>
  );
};

export default ProfilePage;
