# GigFlow - Freelance Marketplace Platform

A full-stack freelance marketplace platform where Clients can post jobs (Gigs) and Freelancers can apply for them (Bids). Built with React, Node.js, Express, MongoDB, and Socket.io for real-time notifications.

## Features

### Core Features
- ✅ **User Authentication**: Secure sign-up and login with JWT tokens stored in HttpOnly cookies
- ✅ **Gig Management**: Create, browse, and search for gigs
- ✅ **Bidding System**: Freelancers can submit bids on open gigs
- ✅ **Hiring Logic**: Clients can hire freelancers with atomic transaction updates
- ✅ **Real-time Notifications**: Socket.io integration for instant notifications when hired

### Bonus Features
- ✅ **Transactional Integrity**: MongoDB transactions prevent race conditions when hiring
- ✅ **Real-time Updates**: Socket.io notifications for hired freelancers

## Tech Stack

### Frontend
- React.js (Vite)
- Tailwind CSS
- Redux Toolkit (State Management)
- React Router (Routing)
- Socket.io Client (Real-time)

### Backend
- Node.js
- Express.js
- MongoDB (Mongoose)
- JWT Authentication (HttpOnly Cookies)
- Socket.io (Real-time)
- bcryptjs (Password Hashing)

## Project Structure

```
gigflow/
├── backend/
│   ├── models/
│   │   ├── User.js
│   │   ├── Gig.js
│   │   └── Bid.js
│   ├── routes/
│   │   ├── auth.js
│   │   ├── gigs.js
│   │   └── bids.js
│   ├── middleware/
│   │   └── auth.js
│   ├── server.js
│   └── package.json
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── store/
│   │   ├── utils/
│   │   └── App.jsx
│   └── package.json
└── README.md
```

## Installation & Setup

### Prerequisites
- Node.js (v16 or higher)
- MongoDB (local installation or MongoDB Atlas)
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the backend directory:
```env
PORT=5000
MONGODB_URI=mongodb://localhost:27017/gigflow
JWT_SECRET=your_super_secret_jwt_key_change_this_in_production
NODE_ENV=development
FRONTEND_URL=http://localhost:5173
```

4. Start the backend server:
```bash
npm run dev
```

The backend server will run on `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the frontend directory (optional):
```env
VITE_API_URL=http://localhost:5000
```

4. Start the development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:5173`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user
- `GET /api/auth/me` - Get current user

### Gigs
- `GET /api/gigs` - Get all open gigs (supports `?search=query` parameter)
- `POST /api/gigs` - Create a new gig (requires authentication)

### Bids
- `POST /api/bids` - Submit a bid for a gig (requires authentication)
- `GET /api/bids/:gigId` - Get all bids for a specific gig (owner only)
- `PATCH /api/bids/:bidId/hire` - Hire a freelancer (atomic transaction)

## Database Schema

### User
```javascript
{
  name: String,
  email: String (unique),
  password: String (hashed),
  createdAt: Date,
  updatedAt: Date
}
```

### Gig
```javascript
{
  title: String,
  description: String,
  budget: Number,
  ownerId: ObjectId (ref: User),
  status: String (enum: ['open', 'assigned']),
  createdAt: Date,
  updatedAt: Date
}
```

### Bid
```javascript
{
  gigId: ObjectId (ref: Gig),
  freelancerId: ObjectId (ref: User),
  message: String,
  price: Number,
  status: String (enum: ['pending', 'hired', 'rejected']),
  createdAt: Date,
  updatedAt: Date
}
```

## Key Features Explained

### 1. Atomic Hiring Logic
The hiring process uses MongoDB transactions to ensure data consistency:
- When a client hires a freelancer, the operation is wrapped in a transaction
- The gig status changes from 'open' to 'assigned'
- The selected bid status changes to 'hired'
- All other bids for the same gig are marked as 'rejected'
- If any step fails, the entire transaction is rolled back

### 2. Real-time Notifications
- Uses Socket.io for real-time communication
- When a freelancer is hired, they receive an instant notification
- Notifications appear as toast messages in the UI
- No page refresh required

### 3. Security Features
- JWT tokens stored in HttpOnly cookies (prevents XSS attacks)
- Password hashing with bcryptjs
- Authentication middleware for protected routes
- CORS configuration for secure cross-origin requests

## Usage

1. **Register/Login**: Create an account or login to existing account
2. **Post a Gig**: Click "Post a Gig" to create a new job posting
3. **Browse Gigs**: View all open gigs on the home page
4. **Search**: Use the search bar to find gigs by title or description
5. **Submit Bid**: Click on a gig to view details and submit a bid
6. **Manage Bids**: Gig owners can view all bids and hire freelancers
7. **Real-time Updates**: Hired freelancers receive instant notifications

## Development

### Running in Development Mode

Backend:
```bash
cd backend
npm run dev
```

Frontend:
```bash
cd frontend
npm run dev
```

### Building for Production

Frontend:
```bash
cd frontend
npm run build
```

Backend:
```bash
cd backend
npm start
```

## Environment Variables

### Backend (.env)
- `PORT` - Server port (default: 5000)
- `MONGODB_URI` - MongoDB connection string
- `JWT_SECRET` - Secret key for JWT tokens
- `NODE_ENV` - Environment (development/production)
- `FRONTEND_URL` - Frontend URL for CORS

### Frontend (.env)
- `VITE_API_URL` - Backend API URL (default: http://localhost:5000)

## Testing the Hiring Flow

1. Create two user accounts (Client and Freelancer)
2. Client posts a gig
3. Freelancer submits a bid
4. Client views bids and clicks "Hire"
5. Freelancer receives real-time notification
6. Gig status changes to "assigned"
7. Other bids are automatically rejected

## License

ISC

## Author

Built as part of a Full Stack Development Internship Assignment
