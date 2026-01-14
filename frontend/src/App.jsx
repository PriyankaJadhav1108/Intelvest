import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { getCurrentUser } from './store/slices/authSlice'
import { initializeSocket } from './utils/socket'

import Navbar from './components/Navbar'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import CreateGig from './pages/CreateGig'
import GigDetails from './pages/GigDetails'
import MyGigs from './pages/MyGigs'
import BidManagement from './pages/BidManagement'
import NotificationToast from './components/NotificationToast'

function App() {
  const dispatch = useDispatch()
  const { isAuthenticated, user } = useSelector((state) => state.auth)

  useEffect(() => {
    // Check if user is authenticated on mount
    dispatch(getCurrentUser())
  }, [dispatch])

  useEffect(() => {
    // Initialize socket connection if user is authenticated
    if (isAuthenticated && user) {
      initializeSocket(user.id, dispatch)
    }
  }, [isAuthenticated, user, dispatch])

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <NotificationToast />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route
          path="/login"
          element={isAuthenticated ? <Navigate to="/" /> : <Login />}
        />
        <Route
          path="/register"
          element={isAuthenticated ? <Navigate to="/" /> : <Register />}
        />
        <Route
          path="/create-gig"
          element={isAuthenticated ? <CreateGig /> : <Navigate to="/login" />}
        />
        <Route path="/gig/:id" element={<GigDetails />} />
        <Route
          path="/my-gigs"
          element={isAuthenticated ? <MyGigs /> : <Navigate to="/login" />}
        />
        <Route
          path="/gig/:gigId/bids"
          element={isAuthenticated ? <BidManagement /> : <Navigate to="/login" />}
        />
      </Routes>
    </div>
  )
}

export default App
