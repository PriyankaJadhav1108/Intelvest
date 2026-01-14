import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Link } from 'react-router-dom'
import { fetchGigs } from '../store/slices/gigSlice'

const Home = () => {
  const dispatch = useDispatch()
  const { gigs, loading } = useSelector((state) => state.gigs)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    dispatch(fetchGigs(searchQuery))
  }, [dispatch, searchQuery])

  const handleSearch = (e) => {
    e.preventDefault()
    dispatch(fetchGigs(searchQuery))
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Find Your Next Gig
        </h1>
        <form onSubmit={handleSearch} className="flex gap-4">
          <input
            type="text"
            placeholder="Search gigs by title or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            type="submit"
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium"
          >
            Search
          </button>
        </form>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : gigs.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">No gigs found. Be the first to post one!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {gigs.map((gig) => (
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
              <div className="text-sm text-gray-500 mb-4">
                Posted by: {gig.ownerId?.name || 'Unknown'}
              </div>
              <Link
                to={`/gig/${gig._id}`}
                className="block w-full text-center bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
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

export default Home
