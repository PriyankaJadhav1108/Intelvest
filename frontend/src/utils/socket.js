import { io } from 'socket.io-client'
import { setNotification } from '../store/slices/bidSlice'

let socket = null

export const initializeSocket = (userId, dispatch) => {
  if (socket) {
    return socket
  }

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'
  socket = io(API_URL, {
    withCredentials: true
  })

  socket.on('connect', () => {
    console.log('Connected to server')
    socket.emit('join_user_room', userId)
  })

  socket.on('hired_notification', (data) => {
    console.log('Hired notification received:', data)
    dispatch(setNotification({
      type: 'success',
      message: data.message,
      gigTitle: data.gigTitle
    }))
  })

  socket.on('disconnect', () => {
    console.log('Disconnected from server')
  })

  return socket
}

export const disconnectSocket = () => {
  if (socket) {
    socket.disconnect()
    socket = null
  }
}

export const getSocket = () => socket
