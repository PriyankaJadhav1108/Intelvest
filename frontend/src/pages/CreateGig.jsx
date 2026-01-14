import { useState, useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useNavigate } from 'react-router-dom'
import { createGig, clearError } from '../store/slices/gigSlice'

const CreateGig = () => {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const { loading, error } = useSelector((state) => state.gigs)

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    budget: ''
  })

  useEffect(() => {
    return () => {
      dispatch(clearError())
    }
  }, [dispatch])

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = await dispatch(createGig(formData))
    if (createGig.fulfilled.match(result)) {
      navigate('/')
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Post a New Gig</h1>

      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg p-6">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <div className="mb-6">
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
            Title
          </label>
          <input
            type="text"
            id="title"
            name="title"
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., Need a website developer"
            value={formData.title}
            onChange={handleChange}
          />
        </div>

        <div className="mb-6">
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
            Description
          </label>
          <textarea
            id="description"
            name="description"
            required
            rows="6"
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="Describe your project in detail..."
            value={formData.description}
            onChange={handleChange}
          />
        </div>

        <div className="mb-6">
          <label htmlFor="budget" className="block text-sm font-medium text-gray-700 mb-2">
            Budget ($)
          </label>
          <input
            type="number"
            id="budget"
            name="budget"
            required
            min="0"
            step="0.01"
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., 500"
            value={formData.budget}
            onChange={handleChange}
          />
        </div>

        <div className="flex gap-4">
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md font-medium disabled:opacity-50"
          >
            {loading ? 'Posting...' : 'Post Gig'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/')}
            className="bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded-md font-medium"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}

export default CreateGig
