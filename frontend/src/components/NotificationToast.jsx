import { useEffect } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { clearNotification } from '../store/slices/bidSlice'

const NotificationToast = () => {
  const { notification } = useSelector((state) => state.bids)
  const dispatch = useDispatch()

  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => {
        dispatch(clearNotification())
      }, 5000)

      return () => clearTimeout(timer)
    }
  }, [notification, dispatch])

  if (!notification) return null

  return (
    <div className="fixed top-20 right-4 z-50 animate-slide-in">
      <div
        className={`${
          notification.type === 'success'
            ? 'bg-green-500'
            : notification.type === 'error'
            ? 'bg-red-500'
            : 'bg-blue-500'
        } text-white px-6 py-4 rounded-lg shadow-lg max-w-md`}
      >
        <div className="flex items-center justify-between">
          <div>
            <p className="font-semibold">{notification.message}</p>
            {notification.gigTitle && (
              <p className="text-sm mt-1">Project: {notification.gigTitle}</p>
            )}
          </div>
          <button
            onClick={() => dispatch(clearNotification())}
            className="ml-4 text-white hover:text-gray-200"
          >
            ✕
          </button>
        </div>
      </div>
    </div>
  )
}

export default NotificationToast
