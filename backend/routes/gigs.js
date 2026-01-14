import express from 'express';
import Gig from '../models/Gig.js';
import { authenticate } from '../middleware/auth.js';

const router = express.Router();

// Get all open gigs (with search query)
router.get('/', async (req, res) => {
  try {
    const { search } = req.query;
    const query = { status: 'open' };

    if (search) {
      query.$or = [
        { title: { $regex: search, $options: 'i' } },
        { description: { $regex: search, $options: 'i' } }
      ];
    }

    const gigs = await Gig.find(query)
      .populate('ownerId', 'name email')
      .sort({ createdAt: -1 });

    res.json({ gigs });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

// Create a new gig
router.post('/', authenticate, async (req, res) => {
  try {
    const { title, description, budget } = req.body;

    if (!title || !description || !budget) {
      return res.status(400).json({ message: 'All fields are required' });
    }

    const gig = new Gig({
      title,
      description,
      budget: Number(budget),
      ownerId: req.userId,
      status: 'open'
    });

    await gig.save();
    await gig.populate('ownerId', 'name email');

    res.status(201).json({ gig });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

export default router;
