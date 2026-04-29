export const validateChatInput = (req, res, next) => {
  const { message, persona } = req.body;

  if (!message || typeof message !== 'string' || message.trim() === '') {
    return res.status(400).json({ error: "Message is required and must be a non-empty string." });
  }

  if (message.length > 500) {
    return res.status(400).json({ error: "Message is too long. Maximum length is 500 characters." });
  }

  const validPersonas = ['general', 'first-time-voter', 'student', 'elderly'];
  if (persona && !validPersonas.includes(persona)) {
    return res.status(400).json({ error: "Invalid persona provided." });
  }

  next();
};
