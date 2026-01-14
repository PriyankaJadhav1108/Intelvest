import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { fetchBidsForGig, hireFreelancer } from '../store/slices/bidSlice'

const BidManagement = () => {
  const { gigId } = useParams()
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const { bids, loading, error } = useSelector((state) => state.bids)

  useEffect(() => {
    dispatch(fetchBidsForGig(gigId))
  }, [dispatch, gigId])

  const handleHire = async (bidId) => {
    if (window.confirm('Are you sure you want to hire this freelancer? This action cannot be undone.')) {
      const result = await dispatch(hireFreelancer(bidId))
      if (hireFreelancer.fulfilled.match(result)) {
        // Refresh bids to show updated statuses
        dispatch(fetchBidsForGig(gigId))
      }
    }
  }

  const getStatusBadge = (status) => {
    const styles = {
      pending: 'bg-yellow-100 text-yellow-800',
      hired: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800'
    }
    return (
      <span
        className={`px-3 py-1 rounded-full text-sm font-medium ${styles[status]}`}
      >
        {status}
      </span>
    )
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <button
          onClick={() => navigate(-1)}
          className="text-blue-600 hover:text-blue-700 mb-4"
        >
          ← Back
        </button>
        <h1 className="text-3xl font-bold text-gray-900">Bids for This Gig</h1>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {bids.length === 0 ? (
        <div className="bg-white shadow-md rounded-lg p-8 text-center">
          <p className="text-gray-500 text-lg">No bids yet for this gig.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {bids.map((bid) => (
            <div
              key={bid._id}
              className={`bg-white shadow-md rounded-lg p-6 ${
                bid.status === 'hired' ? 'border-2 border-green-500' : ''
              }`}
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">
                    {bid.freelancerId?.name || 'Unknown'}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {bid.freelancerId?.email || ''}
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-blue-600 mb-2">
                    ${bid.price}
                  </div>
                  {getStatusBadge(bid.status)}
                </div>
              </div>

              <div className="mb-4">
                <p className="text-gray-700 whitespace-pre-wrap">{bid.message}</p>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">
                  Submitted: {new Date(bid.createdAt).toLocaleDateString()}
                </span>
                {bid.status === 'pending' && (
                  <button
                    onClick={() => handleHire(bid._id)}
                    className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-md font-medium"
                  >
                    Hire This Freelancer
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default BidManagement
