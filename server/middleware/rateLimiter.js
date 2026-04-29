import rateLimit from 'express-rate-limit';

export const chatRateLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  limit: 10, // Limit each IP to 10 requests per `window` (here, per minute).
  standardHeaders: 'draft-7',
  legacyHeaders: false,
  message: {
    error: "Too many requests, please try again later."
  }
});
