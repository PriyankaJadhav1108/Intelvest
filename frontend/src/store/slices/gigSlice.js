import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

// Fetch all gigs
export const fetchGigs = createAsyncThunk(
  'gigs/fetchGigs',
  async (searchQuery = '', { rejectWithValue }) => {
    try {
      const url = searchQuery
        ? `${API_URL}/api/gigs?search=${encodeURIComponent(searchQuery)}`
        : `${API_URL}/api/gigs`
      const response = await axios.get(url)
      return response.data.gigs
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch gigs')
    }
  }
)

// Create a new gig
export const createGig = createAsyncThunk(
  'gigs/createGig',
  async ({ title, description, budget }, { rejectWithValue }) => {
    try {
      const response = await axios.post(
        `${API_URL}/api/gigs`,
        { title, description, budget },
        { withCredentials: true }
      )
      return response.data.gig
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to create gig')
    }
  }
)

const gigSlice = createSlice({
  name: 'gigs',
  initialState: {
    gigs: [],
    loading: false,
    error: null
  },
  reducers: {
    clearError: (state) => {
      state.error = null
    }
  },
  extraReducers: (builder) => {
    builder
      // Fetch gigs
      .addCase(fetchGigs.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchGigs.fulfilled, (state, action) => {
        state.loading = false
        state.gigs = action.payload
      })
      .addCase(fetchGigs.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload
      })
      // Create gig
      .addCase(createGig.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(createGig.fulfilled, (state, action) => {
        state.loading = false
        state.gigs.unshift(action.payload)
      })
      .addCase(createGig.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload
      })
  }
})

export const { clearError } = gigSlice.actions
export default gigSlice.reducer
