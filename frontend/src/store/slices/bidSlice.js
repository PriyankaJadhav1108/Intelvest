import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

// Submit a bid
export const submitBid = createAsyncThunk(
  'bids/submitBid',
  async ({ gigId, message, price }, { rejectWithValue }) => {
    try {
      const response = await axios.post(
        `${API_URL}/api/bids`,
        { gigId, message, price },
        { withCredentials: true }
      )
      return response.data.bid
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to submit bid')
    }
  }
)

// Fetch bids for a gig
export const fetchBidsForGig = createAsyncThunk(
  'bids/fetchBidsForGig',
  async (gigId, { rejectWithValue }) => {
    try {
      const response = await axios.get(`${API_URL}/api/bids/${gigId}`, {
        withCredentials: true
      })
      return response.data.bids
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch bids')
    }
  }
)

// Hire a freelancer
export const hireFreelancer = createAsyncThunk(
  'bids/hireFreelancer',
  async (bidId, { rejectWithValue }) => {
    try {
      const response = await axios.patch(
        `${API_URL}/api/bids/${bidId}/hire`,
        {},
        { withCredentials: true }
      )
      return response.data
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to hire freelancer')
    }
  }
)

const bidSlice = createSlice({
  name: 'bids',
  initialState: {
    bids: [],
    loading: false,
    error: null,
    notification: null
  },
  reducers: {
    clearError: (state) => {
      state.error = null
    },
    setNotification: (state, action) => {
      state.notification = action.payload
    },
    clearNotification: (state) => {
      state.notification = null
    }
  },
  extraReducers: (builder) => {
    builder
      // Submit bid
      .addCase(submitBid.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(submitBid.fulfilled, (state) => {
        state.loading = false
      })
      .addCase(submitBid.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload
      })
      // Fetch bids
      .addCase(fetchBidsForGig.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchBidsForGig.fulfilled, (state, action) => {
        state.loading = false
        state.bids = action.payload
      })
      .addCase(fetchBidsForGig.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload
      })
      // Hire freelancer
      .addCase(hireFreelancer.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(hireFreelancer.fulfilled, (state, action) => {
        state.loading = false
        // Update bid status in the list
        const bidIndex = state.bids.findIndex(
          bid => bid._id === action.payload.bid._id
        )
        if (bidIndex !== -1) {
          state.bids[bidIndex] = action.payload.bid
          // Mark all other bids as rejected
          state.bids.forEach((bid, index) => {
            if (index !== bidIndex && bid.gigId === action.payload.bid.gigId) {
              bid.status = 'rejected'
            }
          })
        }
      })
      .addCase(hireFreelancer.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload
      })
  }
})

export const { clearError, setNotification, clearNotification } = bidSlice.actions
export default bidSlice.reducer
