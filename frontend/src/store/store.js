import { configureStore } from '@reduxjs/toolkit'
import authReducer from './slices/authSlice'
import gigReducer from './slices/gigSlice'
import bidReducer from './slices/bidSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    gigs: gigReducer,
    bids: bidReducer
  }
})
