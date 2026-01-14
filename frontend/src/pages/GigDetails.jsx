import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useSelector } from 'react-redux'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

const GigDetails = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { isAuthenticated, user } = useSelector((state) => state.auth)
  const [gig, setGig] = useState(null)
  const [loading, setLoading] = useState(true)
  const [bidForm, setBidForm] = useState({
    message: '',
    price: ''
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchGig = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/gigs`)
        const foundGig = response.data.gigs.find((g) => g._id === id)
        if (foundGig) {
          setGig(foundGig)
        } else {
          setError('Gig not found')
        }
      } catch (err) {
        setError('Failed to load gig')
      } finally {
        setLoading(false)
      }
    }

    fetchGig()
  }, [id])

  const handleBidSubmit = async (e) => {
    e.preventDefault()
    if (!isAuthenticated) {
      navigate('/login')
      return
    }

    setSubmitting(true)
    setError(null)

    try {
      await axios.post(
        `${API_URL}/api/bids`,
        {
          gigId: id,
          message: bidForm.message,
          price: bidForm.price
        },
        { withCredentials: true }
      )
      alert('Bid submitted successfully!')
      setBidForm({ message: '', price: '' })
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to submit bid')
    } finally {
      setSubmitting(false)
    }
  }

  const isOwner = gig && user && gig.ownerId._id?.toString() === user.id?.toString()

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    )
  }

  if (error && !gig) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      </div>
    )
  }

  if (!gig) return null

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <div className="flex justify-between items-start mb-4">
          <h1 className="text-3xl font-bold text-gray-900">{gig.title}</h1>
          <span
            className={`px-3 py-1 rounded-full text-sm font-medium ${
              gig.status === 'open'
                ? 'bg-green-100 text-green-800'
                : 'bg-gray-100 text-gray-800'
            }`}
          >
            {gig.status}
          </span>
        </div>

        <div className="mb-4">
          <p className="text-gray-700 whitespace-pre-wrap">{gig.description}</p>
        </div>

        <div className="flex items-center justify-between mb-4">
          <div>
            <span className="text-sm text-gray-500">Budget:</span>
            <span className="text-2xl font-bold text-blue-600 ml-2">
              ${gig.budget}
            </span>
          </div>
          <div className="text-sm text-gray-500">
            Posted by: {gig.ownerId?.name || 'Unknown'}
          </div>
        </div>

        {isOwner && gig.status === 'open' && (
          <Link
            to={`/gig/${gig._id}/bids`}
            className="block w-full text-center bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            View Bids
          </Link>
        )}
      </div>

      {isAuthenticated && !isOwner && gig.status === 'open' && (
        <div className="bg-white shadow-md rounded-lg p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Submit a Bid</h2>
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}
          <form onSubmit={handleBidSubmit}>
            <div className="mb-4">
              <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-2">
                Your Proposal
              </label>
              <textarea
                id="message"
                name="message"
                required
                rows="4"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Describe why you're the best fit for this project..."
                value={bidForm.message}
                onChange={(e) =>
                  setBidForm({ ...bidForm, message: e.target.value })
                }
              />
            </div>
            <div className="mb-4">
              <label htmlFor="price" className="block text-sm font-medium text-gray-700 mb-2">
                Your Price ($)
              </label>
              <input
                type="number"
                id="price"
                name="price"
                required
                min="0"
                step="0.01"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., 450"
                value={bidForm.price}
                onChange={(e) =>
                  setBidForm({ ...bidForm, price: e.target.value })
                }
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md font-medium disabled:opacity-50"
            >
              {submitting ? 'Submitting...' : 'Submit Bid'}
            </button>
          </form>
        </div>
      )}

      {!isAuthenticated && gig.status === 'open' && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
          <p className="text-blue-800 mb-2">
            Please{' '}
            <Link to="/login" className="font-semibold underline">
              login
            </Link>{' '}
            to submit a bid
          </p>
        </div>
      )}
    </div>
  )
}

export default GigDetails
