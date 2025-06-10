const express = require('express');
const OpenAI = require('openai');
const cors = require('cors');
const rateLimit = require('express-rate-limit');

const app = express();
const port = process.env.PORT || 3000;

// Initialize OpenAI
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});
app.use(limiter);

// In-memory conversation storage (use Redis in production)
const conversations = new Map();

// Conversation cleanup (remove old conversations)
setInterval(() => {
  const now = Date.now();
  const maxAge = 30 * 60 * 1000; // 30 minutes
  
  for (const [key, value] of conversations.entries()) {
    if (now - value.lastUsed > maxAge) {
      conversations.delete(key);
    }
  }
}, 5 * 60 * 1000); // Clean every 5 minutes

// Generate conversation ID
function generateConversationId() {
  return Math.random().toString(36).substring(2, 8).toUpperCase();
}

// Main chat endpoint for Nightbot
app.get('/chat', async (req, res) => {
  try {
    const { user, message } = req.query;
    
    if (!message) {
      return res.status(400).send('Message parameter is required');
    }

    // Check if message starts with conversation ID
    const conversationIdMatch = message.match(/^([A-Z0-9]{6})\s+(.+)$/);
    let conversationId = null;
    let actualMessage = message;

    if (conversationIdMatch) {
      conversationId = conversationIdMatch[1];
      actualMessage = conversationIdMatch[2];
    }

    // Get or create conversation
    let conversation;
    if (conversationId && conversations.has(conversationId)) {
      conversation = conversations.get(conversationId);
      conversation.lastUsed = Date.now();
    } else {
      conversationId = generateConversationId();
      conversation = {
        id: conversationId,
        messages: [
          {
            role: 'system',
            content: `You are a helpful AI assistant in a Twitch/YouTube live stream chat. Keep responses concise (under 400 characters) and engaging. You can help with questions, create content ideas, or just have fun conversations. The current user is ${user || 'Anonymous'}.`
          }
        ],
        lastUsed: Date.now()
      };
      conversations.set(conversationId, conversation);
    }

    // Add user message to conversation
    conversation.messages.push({
      role: 'user',
      content: actualMessage
    });

    // Call OpenAI API
    const completion = await openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: conversation.messages,
      max_tokens: 150,
      temperature: 0.7,
      presence_penalty: 0.6,
      frequency_penalty: 0.3
    });

    const aiResponse = completion.choices[0].message.content.trim();
    
    // Add AI response to conversation
    conversation.messages.push({
      role: 'assistant',
      content: aiResponse
    });

    // Keep conversation history manageable
    if (conversation.messages.length > 20) {
      // Keep system message and last 18 messages
      conversation.messages = [
        conversation.messages[0],
        ...conversation.messages.slice(-18)
      ];
    }

    // Format response for Nightbot
    const response = `${aiResponse} [${conversationId}]`;
    
    res.send(response);

  } catch (error) {
    console.error('Error:', error);
    
    if (error.status === 429) {
      res.status(429).send('Rate limit exceeded. Please try again later.');
    } else if (error.status === 401) {
      res.status(500).send('API key error. Please contact administrator.');
    } else {
      res.status(500).send('Sorry, I encountered an error. Please try again.');
    }
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    conversations: conversations.size
  });
});

// Stats endpoint
app.get('/stats', (req, res) => {
  res.json({
    activeConversations: conversations.size,
    uptime: process.uptime(),
    memoryUsage: process.memoryUsage()
  });
});

// Start server
app.listen(port, () => {
  console.log(`🤖 Nightbot AI Chatbot API running on port ${port}`);
  console.log(`📡 Chat endpoint: http://localhost:${port}/chat?user=$(user)&message=$(query)`);
});

module.exports = app;
