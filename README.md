# E-Shop Customer Support Chatbot 🤖

An intelligent AI-powered customer support chatbot built for an e-commerce platform. This project demonstrates key AI techniques including knowledge representation, inference engines, natural language processing, and intelligent agent architecture.

## 📚 Project Overview

This chatbot serves as an automated customer support system for an online e-commerce store. It can handle various customer inquiries including order tracking, product recommendations, return policies, shipping information, and more.

### AI Techniques Demonstrated

This project implements several core AI concepts from the **AI Techniques and Agent Technology** curriculum:

1. **Intelligent Agents (Unit 9)** - Complete agent architecture with perception, reasoning, and action
2. **Knowledge Representation (Unit 4)** - Production system with facts and rules
3. **Inference Engine (Unit 1, Unit 5)** - Forward chaining for rule-based reasoning
4. **Natural Language Processing (Unit 1)** - Intent classification and entity extraction
5. **Expert Systems** - Rule-based decision making for customer support

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface (UI)                   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Customer Support Agent                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Perception  │→ │  Reasoning   │→ │    Action    │ │
│  │ (NLP Process)│  │ (Inference)  │  │  (Execute)   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼────────┐      ┌────────▼─────────┐
│ Knowledge Base │      │ Inference Engine │
│  - Products    │      │ - Forward Chain  │
│  - Orders      │      │ - Rule Matching  │
│  - Policies    │      │ - Conflict Res.  │
│  - Rules       │      └──────────────────┘
└────────────────┘
```

## 🚀 Features

- **Order Tracking**: Check order status with order ID (e.g., ORD12345)
- **Product Recommendations**: Get personalized product suggestions based on category and price
- **Return Policy**: Learn about return policies and check product returnability
- **Shipping Information**: View shipping options and delivery times
- **Product Information**: Get detailed information about specific products
- **Warranty Information**: Check warranty coverage for different product categories
- **Payment Methods**: Learn about accepted payment options
- **Order Cancellation**: Request order cancellation assistance

## 📋 Requirements

- Python 3.7 or higher
- No external dependencies required (uses only Python standard library)

## 🔧 Installation

1. Clone or download this repository
2. Ensure Python 3.7+ is installed on your system
3. Navigate to the project directory

```bash
cd e-shop-chatbot
```

## ▶️ Usage

Run the chatbot using:

```bash
python main.py
```

### Example Interactions

```
👤 You: Hello
🤖 Chatbot: Hello! Welcome to E-Shop Customer Support...

👤 You: What's the status of order ORD12345?
🤖 Chatbot: 📦 Order Status for ORD12345:
Product: Wireless Bluetooth Headphones
Status: Shipped
...

👤 You: Show me electronics under $100
🤖 Chatbot: 🛍️ Product Recommendations:
1. Wireless Bluetooth Headphones - $79.99
...

👤 You: What's your return policy?
🤖 Chatbot: 🔄 Return Policy:
Items can be returned within 30 days...
```

### Commands

- Type your question naturally
- Use `help` for assistance
- Use `exit`, `quit`, or `bye` to end the session

## 📁 Project Structure

```
e-shop-chatbot/
│
├── main.py                 # Entry point
├── README.md              # This file
│
├── src/
│   ├── agent.py           # Intelligent agent implementation
│   ├── inference_engine.py # Forward chaining inference
│   ├── knowledge_base.py  # Knowledge representation
│   ├── nlp_processor.py   # NLP for intent & entity extraction
│   └── ui.py              # Command-line interface
│
└── data/
    ├── products.json      # Product catalog
    ├── orders.json        # Order database
    ├── policies.json      # Store policies
    └── rules.json         # Production rules
```

## 🧠 Technical Details

### Agent Architecture

The `CustomerSupportAgent` follows a classic agent architecture:

1. **Perceive**: Process user input using NLP
   - Text preprocessing
   - Intent classification
   - Entity extraction (order IDs, product IDs, prices, categories)

2. **Reason**: Use inference engine to select appropriate action
   - Forward chaining algorithm
   - Rule matching based on current facts
   - Conflict resolution using priority

3. **Act**: Execute the selected action and generate response
   - Query knowledge base
   - Format response
   - Update conversation context

### Inference Engine

Implements **forward chaining** with three phases:

1. **Match Phase**: Find all rules whose conditions match current facts
2. **Conflict Resolution**: Select rule with highest priority
3. **Execute Phase**: Fire the selected rule

### Knowledge Base

Uses a **production system** approach:

- **Working Memory**: Current conversation state (facts)
- **Production Memory**: IF-THEN rules
- **Data Store**: Products, orders, and policies

### NLP Processing

Simple but effective NLP using:

- **Keyword matching** for intent classification
- **Regex patterns** for entity extraction
- **Text preprocessing** for normalization

## 📊 Sample Data

The system includes:

- **15 Products** across categories (Electronics, Sports, Home, Accessories)
- **10 Sample Orders** with various statuses
- **12 Production Rules** for different intents
- **Complete Policies** (return, shipping, warranty)

## 🎓 Educational Value

This project demonstrates:

- ✅ Practical implementation of AI agent architecture
- ✅ Rule-based expert system design
- ✅ Forward chaining inference algorithm
- ✅ Knowledge representation using production systems
- ✅ Basic NLP techniques for intent classification
- ✅ Modular, maintainable code structure
- ✅ Real-world application of AI techniques

## 🔮 Future Enhancements

Possible improvements:

- Machine learning-based intent classification
- Sentiment analysis for customer satisfaction
- Integration with actual e-commerce APIs
- Multi-language support
- Voice interface
- Backward chaining for complex queries
- Learning from conversation history

## 📝 License

This project is created for educational purposes as part of the AI Techniques and Agent Technology course.

## 👨‍💻 Author

Created as a mini project for AI Techniques and Agent Technology degree program.

## 🙏 Acknowledgments

- Course instructors and materials
- AI and Expert Systems textbooks
- Python community

---

**Note**: This is an educational project demonstrating AI concepts. For production use, consider adding error handling, logging, database integration, and security features.
