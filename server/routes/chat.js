import express from 'express';
import { generateChatResponse } from '../services/geminiService.js';
import { validateChatInput } from '../middleware/inputValidator.js';
import { chatRateLimiter } from '../middleware/rateLimiter.js';

const router = express.Router();

router.post('/', chatRateLimiter, validateChatInput, async (req, res) => {
  console.log(`[VoteWise] POST /api/chat received from ${req.ip}`);
  try {
    const { message, persona, context } = req.body;
    const response = await generateChatResponse(message, persona, context);
    console.log(`[VoteWise] POST /api/chat response sent | blocked=${response.safety?.blocked}`);
    res.json(response);
  } catch (error) {
    const statusCode = error.statusCode || 500;
    console.error(`[VoteWise] POST /api/chat error | status=${statusCode} | message=${error.message}`);
    res.status(statusCode).json({ error: error.message || "An error occurred." });
  }
});

export default router;
