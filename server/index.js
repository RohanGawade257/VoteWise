import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import dotenv from 'dotenv';
import chatRoutes from './routes/chat.js';
import path from 'path';
import { fileURLToPath } from 'url';

import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const envPath = path.join(__dirname, '.env');
const rootEnvPath = path.join(__dirname, '../.env');

if (fs.existsSync(envPath)) {
  dotenv.config({ path: envPath });
} else if (fs.existsSync(rootEnvPath)) {
  dotenv.config({ path: rootEnvPath });
} else {
  dotenv.config();
}

const app = express();
const PORT = process.env.PORT || 8080;

// Security middleware
app.use(helmet({
  contentSecurityPolicy: false, // Disabling temporarily to allow React scripts in production
  crossOriginEmbedderPolicy: false
}));

// CORS configuration
const allowedOrigin = process.env.NODE_ENV === 'production' 
  ? '*' // In production, we'll serve from the same domain mostly, but this allows flexibility
  : process.env.ALLOWED_ORIGIN || 'http://localhost:5173';

app.use(cors({
  origin: allowedOrigin,
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type']
}));

// Body parser
app.use(express.json());

// Routes
// Request logger (no secrets)
app.use((req, _res, next) => {
  console.log(`[VoteWise] ${req.method} ${req.path} from ${req.ip}`);
  next();
});

// Routes
app.use('/api/chat', chatRoutes);

// Health check — both /health (legacy) and /api/health
const healthHandler = (_req, res) => {
  const hasKey = !!process.env.GEMINI_API_KEY;
  res.status(200).json({ ok: true, geminiKeyPresent: hasKey, timestamp: new Date() });
};
app.get('/health', healthHandler);
app.get('/api/health', healthHandler);



// Serve static frontend in production
if (process.env.NODE_ENV === 'production') {
  const clientBuildPath = path.join(__dirname, '../client/dist');
  app.use(express.static(clientBuildPath));

  app.get('*', (req, res) => {
    res.sendFile(path.join(clientBuildPath, 'index.html'));
  });
}

// Start server
app.listen(PORT, () => {
  console.log(`VoteWise Backend running on port ${PORT}`);
  console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
});
