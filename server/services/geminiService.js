import { GoogleGenerativeAI } from "@google/generative-ai";
import { SYSTEM_PROMPT, getContextPrompt } from "../prompts/systemPrompt.js";

const MODEL_NAME = "gemini-2.0-flash";

export const generateChatResponse = async (message, persona, pageContext) => {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    console.error("[VoteWise] GEMINI_API_KEY is not set in environment.");
    const err = new Error("API key configuration issue. Please contact the site administrator.");
    err.statusCode = 503;
    throw err;
  }

  console.log(`[VoteWise] Chat request | persona="${persona}" | model="${MODEL_NAME}" | msgLen=${message.length}`);

  const genAI = new GoogleGenerativeAI(apiKey);
  const model = genAI.getGenerativeModel({
    model: MODEL_NAME,
    systemInstruction: SYSTEM_PROMPT,
  });

  const fullPrompt = `${getContextPrompt(persona, pageContext)}\n\nUser Question: ${message}`;

  try {
    const result = await model.generateContent(fullPrompt);
    const responseText = result.response.text();
    console.log(`[VoteWise] Gemini response OK | length=${responseText.length}`);

    return {
      answer: responseText,
      sourceReminder: "Verify official info at eci.gov.in or voters.eci.gov.in",
      safety: { blocked: false, reason: null }
    };

  } catch (error) {
    const status = error.status || error.statusCode || 'unknown';
    console.error(`[VoteWise] Gemini API error | status=${status} | message=${error.message?.slice(0, 120)}`);

    if (status === 429) {
      const friendly = new Error("Rate limit or quota exceeded. Please wait a moment and try again.");
      friendly.statusCode = 429;
      throw friendly;
    }

    if (status === 401 || status === 403) {
      const friendly = new Error("API key configuration issue. Please contact the site administrator.");
      friendly.statusCode = 403;
      throw friendly;
    }

    if (error.message?.includes('SAFETY') || error.message?.includes('blocked')) {
      return {
        answer: "I'm unable to respond to this request. Please ask about the Indian election process or voting guidelines.",
        sourceReminder: "",
        safety: { blocked: true, reason: "Content flagged by safety filters." }
      };
    }

    if (status === 503 || error.message?.includes('overloaded')) {
      const friendly = new Error("Gemini AI is temporarily overloaded. Please try again shortly.");
      friendly.statusCode = 503;
      throw friendly;
    }

    const friendly = new Error("Something went wrong with the AI service. Please try again.");
    friendly.statusCode = 500;
    throw friendly;
  }
};
