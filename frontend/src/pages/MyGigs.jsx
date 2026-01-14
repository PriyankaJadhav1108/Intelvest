import { useEffect, useState } from 'react'
import { useSelector } from 'react-redux'
import { Link } from 'react-router-dom'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

const MyGigs = () => {
  const { user } = useSelector((state) => state.auth)
  const [myGigs, setMyGigs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchMyGigs = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/gigs`)
        // Filter gigs owned by current user
        const userGigs = response.data.gigs.filter(
          (gig) => gig.ownerId._id?.toString() === user.id?.toString()
        )
        setMyGigs(userGigs)
      } catch (error) {
        console.error('Failed to fetch gigs:', error)
      } finally {
        setLoading(false)
      }
    }

    if (user) {
      fetchMyGigs()
    }
  }, [user])

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">My Gigs</h1>
        <Link
          to="/create-gig"
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
        >
          Post New Gig
        </Link>
      </div>

      {myGigs.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg mb-4">You haven't posted any gigs yet.</p>
          <Link
            to="/create-gig"
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            Post your first gig →
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {myGigs.map((gig) => (
            <div
              key={gig._id}
              className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
            >
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                {gig.title}
              </h2>
              <p className="text-gray-600 mb-4 line-clamp-3">
                {gig.description}
              </p>
              <div className="flex items-center justify-between mb-4">
                <span className="text-2xl font-bold text-blue-600">
                  ${gig.budget}
                </span>
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
              {gig.status === 'open' && (
                <Link
                  to={`/gig/${gig._id}/bids`}
                  className="block w-full text-center bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  View Bids
                </Link>
              )}
              <Link
                to={`/gig/${gig._id}`}
                className="block w-full text-center mt-2 text-blue-600 hover:text-blue-700 px-4 py-2 rounded-lg font-medium"
              >
                View Details
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default MyGigs
