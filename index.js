const express = require('express');
const cors = require('cors');
const rateLimit = require('express-rate-limit');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Rate limiting to prevent abuse
const limiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 30, // limit each IP to 30 requests per windowMs
  message: 'Too many requests, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
});

app.use('/api/', limiter);

// Simple AI responses (you can replace this with actual AI API calls)
const getAIResponse = (message) => {
  const responses = {
    'hello': 'Hello! How can I help you today?',
    'hi': 'Hi there! What would you like to know?',
    'how are you': 'I\'m doing great! Thanks for asking.',
    'what is your name': 'I\'m an AI assistant created to help answer questions.',
    'bye': 'Goodbye! Have a great day!',
    'goodbye': 'See you later!',
    'thanks': 'You\'re welcome!',
    'thank you': 'Happy to help!',
    'why sky is blue': 'The sky appears blue because of a phenomenon called Rayleigh scattering. When sunlight enters Earth\'s atmosphere, it collides with gas molecules. Blue light waves are shorter and get scattered more than other colors, making the sky appear blue to our eyes.',
    'what is ai': 'AI (Artificial Intelligence) refers to computer systems that can perform tasks that typically require human intelligence, such as learning, reasoning, and problem-solving.',
    'help': 'I can answer questions about various topics! Try asking me about science, technology, or general knowledge.',
  };

  const lowerMessage = message.toLowerCase().trim();
  
  // Check for exact matches first
  if (responses[lowerMessage]) {
    return responses[lowerMessage];
  }
  
  // Check for partial matches
  for (const [key, value] of Object.entries(responses)) {
    if (lowerMessage.includes(key)) {
      return value;
    }
  }
  
  // Default responses for unknown queries
  const defaultResponses = [
    'That\'s an interesting question! I\'m still learning about that topic.',
    'I\'m not sure about that specific question, but I\'d be happy to help with something else!',
    'That\'s beyond my current knowledge, but feel free to ask me about other topics!',
    'I don\'t have information about that right now. Try asking about science, technology, or general knowledge!',
  ];
  
  return defaultResponses[Math.floor(Math.random() * defaultResponses.length)];
};

// Routes
app.get('/', (req, res) => {
  res.json({
    message: '🤖 AI Chatbot API is running!',
    status: 'online',
    version: '1.0.0',
    endpoints: {
      chat: '/api/chat?message=your_message',
      health: '/health'
    }
  });
});

app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// Main chat endpoint for Nightbot
app.get('/api/chat', (req, res) => {
  try {
    const message = req.query.message;
    
    if (!message) {
      return res.status(400).json({
        error: 'Message parameter is required',
        usage: 'GET /api/chat?message=your_question'
      });
    }
    
    if (message.length > 500) {
      return res.status(400).json({
        error: 'Message too long. Please keep it under 500 characters.'
      });
    }
    
    const aiResponse = getAIResponse(message);
    
    // Return just the text for Nightbot (simple format)
    res.send(aiResponse);
    
  } catch (error) {
    console.error('Error processing chat request:', error);
    res.status(500).send('Sorry, I encountered an error processing your request.');
  }
});

// POST endpoint for more complex integrations
app.post('/api/chat', (req, res) => {
  try {
    const { message, user, context } = req.body;
    
    if (!message) {
      return res.status(400).json({
        error: 'Message is required in request body'
      });
    }
    
    if (message.length > 500) {
      return res.status(400).json({
        error: 'Message too long. Please keep it under 500 characters.'
      });
    }
    
    const aiResponse = getAIResponse(message);
    
    res.json({
      response: aiResponse,
      user: user || 'anonymous',
      timestamp: new Date().toISOString(),
      context: context || null
    });
    
  } catch (error) {
    console.error('Error processing POST chat request:', error);
    res.status(500).json({
      error: 'Internal server error',
      message: 'Sorry, I encountered an error processing your request.'
    });
  }
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Endpoint not found',
    availableEndpoints: [
      'GET /',
      'GET /health',
      'GET /api/chat?message=your_message',
      'POST /api/chat'
    ]
  });
});

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('Unhandled error:', error);
  res.status(500).json({
    error: 'Internal server error',
    message: 'Something went wrong!'
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 AI Chatbot server is running on port ${PORT}`);
  console.log(`📡 Health check: http://localhost:${PORT}/health`);
  console.log(`💬 Chat endpoint: http://localhost:${PORT}/api/chat?message=test`);
});
