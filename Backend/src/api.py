import os
import logging
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Flask, request, jsonify
import jwt
import bcrypt

from src.database import Database, DatabaseConnectionError, ConfigurationError
from src.knowledge_base import KnowledgeBase
from src.inference_engine import InferenceEngine
from src.nlp_processor import NLPProcessor
from src.ai_nlp_processor import AINLPProcessor
from src.conversation_context import ConversationContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24*30

# Global database and agent components
db = None
kb = None
inference_engine = None
nlp = None
ai_nlp = None
conversation_contexts = {}  # Store conversation contexts per session


def init_app():
    """Initialize database connection and agent components."""
    global db, kb, inference_engine, nlp, ai_nlp
    
    try:
        db = Database()
        db.connect()
        kb = KnowledgeBase(db)
        inference_engine = InferenceEngine(kb)
        nlp = NLPProcessor()  # Keep for backward compatibility
        
        # Initialize AI NLP Processor
        try:
            ai_nlp = AINLPProcessor()
            logger.info("AI NLP Processor initialized successfully")
        except Exception as e:
            logger.warning(f"AI NLP Processor initialization failed, using fallback: {e}")
            ai_nlp = None
        
        logger.info("API initialized successfully")
    except (DatabaseConnectionError, ConfigurationError) as e:
        logger.error(f"Failed to initialize API: {e}")
        raise


def process_message(user_input, user_context=None, conversation_context=None):
   
    if user_context is None:
        user_context = {'user_id': None, 'role': 'guest'}
    
    # Get context for follow-up questions
    context_data = None
    if conversation_context:
        context_data = conversation_context.get_context()
    
    # Perception phase - Use AI NLP if available, otherwise fallback
    if ai_nlp is not None:
        # Use AI NLP processor
        nlp_result = ai_nlp.process(user_input, context=context_data)
        
        intent = nlp_result['intent']
        entities = nlp_result['entities']
        processed_text = nlp_result['processed_input']
        confidence = nlp_result['confidence']
        used_fallback = nlp_result['used_fallback']
        all_intent_scores = nlp_result.get('all_intent_scores', {})
        is_ambiguous = nlp_result.get('is_ambiguous', False)
        ambiguous_intents = nlp_result.get('ambiguous_intents', [])
        needs_clarification = nlp_result.get('needs_clarification', False)
        
        logger.debug(
            f"AI NLP: intent={intent}, confidence={confidence:.2f}, "
            f"fallback={used_fallback}, ambiguous={is_ambiguous}"
        )
        
        # Handle ambiguous intents - ask clarifying question (Requirement 8.2)
        if is_ambiguous and ambiguous_intents:
            clarification = ai_nlp.generate_clarification_question(ambiguous_intents)
            return clarification
        
        # Handle low confidence - provide suggestions (Requirement 8.1, 8.3)
        if needs_clarification and confidence < ai_nlp.config.confidence_threshold:
            suggestions = ai_nlp.generate_low_confidence_suggestions()
            return suggestions
        
        # Handle topic change if conversation context exists
        if conversation_context:
            if conversation_context.detect_topic_change(intent):
                conversation_context.clear()
                logger.debug(f"Topic change detected, cleared context")
        
        perception = {
            'intent': intent,
            'raw_input': user_input,
            'processed_input': processed_text,
            'user_context': user_context,
            'confidence': confidence,
            'used_fallback': used_fallback,
            'all_intent_scores': all_intent_scores,
            **entities
        }
    else:
        # Fallback to original keyword-based NLP
        processed_text = nlp.preprocess_text(user_input)
        intent = nlp.classify_intent(processed_text)
        entities = nlp.extract_entities(processed_text)
        
        perception = {
            'intent': intent,
            'raw_input': user_input,
            'processed_input': processed_text,
            'user_context': user_context,
            'confidence': 0.5,  # Default confidence for keyword matching
            'used_fallback': True,
            **entities
        }
    
    # Reasoning phase
    rule = inference_engine.infer(perception)
    
    # Action phase
    if not rule:
        # No rule matched - provide helpful suggestions (Requirement 8.3)
        if ai_nlp is not None:
            return ai_nlp.generate_low_confidence_suggestions()
        else:
            return ("I'm not sure I understood that correctly.\n\n"
                    "I can help you with:\n"
                    "  • Order status (provide order number)\n"
                    "  • Return policy\n"
                    "  • Product recommendations\n"
                    "  • General inquiries\n\n"
                    "Could you please rephrase your question?")
    
    action = rule['action']
    response = execute_action(action, perception)
    
    # Update conversation context if available
    if conversation_context:
        conversation_context.add_exchange(
            user_input=user_input,
            intent=perception['intent'],
            entities=entities if ai_nlp else perception,
            response=response
        )
    
    return response


def execute_action(action, perception):
    action_handlers = {
        'get_order_status': handle_order_status,
        'request_order_id': handle_request_order_id,
        'get_return_policy': handle_return_policy,
        'check_product_returnability': handle_product_returnability,
        'recommend_products': handle_recommend_products,
        'get_product_info': handle_product_info,
        'get_shipping_policy': handle_shipping_policy,
        'provide_general_help': handle_general_help,
        'greet_user': handle_greet,
        'get_warranty_info': handle_warranty_info,
        'get_payment_info': handle_payment_info,
        'handle_cancellation': handle_cancellation,
        'get_order_history': handle_order_history,
        'get_user_profile': handle_user_profile
    }
    
    handler = action_handlers.get(action)
    if handler:
        return handler(perception)
    return "I'm sorry, I couldn't process that request."


def handle_order_status(perception):
    
    order_id = perception.get('order_id')
    user_context = perception.get('user_context', {'role': 'guest'})
    user_role = user_context.get('role', 'guest')
    user_id = user_context.get('user_id')
    
    # If no order_id provided, check if user is authenticated and can see their orders
    if not order_id:
        if user_id:
            # Authenticated user - offer to show their recent orders
            return ("I'd be happy to check your order status!\n\n"
                    "Please provide your order number (format: ORD12345), "
                    "or ask me to 'show my orders' to see your recent orders.")
        else:
            return handle_request_order_id(perception)
    
    # Query order from database
    order = kb.get_order(order_id)
    
    if order:
        product = kb.get_product(order['product_id'])
        product_name = product['name'] if product else "your item"
        
        response = f" Order Status for {order_id}:\n\n"
        response += f"Product: {product_name}\n"
        response += f"Status: {order['status']}\n"
        response += f"Order Date: {order['order_date']}\n"
        
        if order['status'] != 'Cancelled':
            response += f"Expected Delivery: {order['delivery_date']}\n"
            if order.get('tracking_number'):
                response += f"Tracking Number: {order['tracking_number']}\n"
        
        response += f"Quantity: {order['quantity']}\n"
        response += f"Total: ${order['total']:.2f}"
        
        # Add status-specific helpful information
        if order['status'] == 'Processing':
            response += "\n\n Your order is being prepared for shipment."
        elif order['status'] == 'Shipped':
            response += "\n\n Your order is on its way!"
        elif order['status'] == 'Delivered':
            response += "\n\n Your order has been delivered."
        elif order['status'] == 'Cancelled':
            response += "\n\n This order has been cancelled."
        
        # Add personalized message for authenticated users
        if user_role == 'customer' and user_id:
            response += "\n\nAs a registered customer, your chat history is saved."
        elif user_role == 'admin':
            response += "\n\n🔧 Admin access: Full order details available."
        
        return response
    else:
        return (f"I couldn't find order {order_id}.\n\n"
                "Please check the order number and try again. "
                "Order numbers are in the format ORD12345.")


def handle_request_order_id(perception):
    return "I'd be happy to check your order status! \n\nPlease provide your order number (format: ORD12345)."


def handle_return_policy(perception):
    policy = kb.get_return_policy()
    
    if not policy:
        return "Return policy information is currently unavailable."
    
    response = "Return Policy:\n\n"
    response += f"{policy.get('general', '')}\n\n"
    
    if 'conditions' in policy:
        response += "Conditions:\n"
        for condition in policy['conditions']:
            response += f"  • {condition}\n"
    
    if 'non_returnable_categories' in policy:
        response += "\nNon-returnable items:\n"
        for category in policy['non_returnable_categories']:
            response += f"  • {category}\n"
    
    if 'process' in policy:
        response += "\nReturn Process:\n"
        for i, step in enumerate(policy['process'], 1):
            response += f"  {i}. {step}\n"
    
    return response


def handle_product_returnability(perception):
    """Check if specific product is returnable."""
    product_id = perception.get('product_id')
    product = kb.get_product(product_id)
    
    if product:
        if product['returnable']:
            return f"{product['name']} is returnable within {product['return_window']} days of delivery."
        else:
            return f"{product['name']} is non-returnable."
    else:
        return handle_return_policy(perception)


def handle_recommend_products(perception):
    
    category = perception.get('category')
    max_price = perception.get('max_price')
    min_price = perception.get('min_price')
    features = perception.get('features', [])
    product_name = perception.get('product_name')
    user_context = perception.get('user_context', {'role': 'guest'})
    user_id = user_context.get('user_id')
    
    # If specific filters are provided, use filtered search
    if category or max_price or min_price or features or product_name:
        # Try advanced search if we have name or features
        if product_name or features:
            feature_query = features[0] if features else None
            products = kb.search_products_advanced(
                name=product_name,
                feature=feature_query,
                category=category
            )
            
            if max_price is not None:
                products = [p for p in products if p['price'] <= max_price]
            if min_price is not None:
                products = [p for p in products if p['price'] >= min_price]
        else:
            products = kb.search_products(category=category, max_price=max_price)
            
            if min_price is not None:
                products = [p for p in products if p['price'] >= min_price]
        
        if not products:
            criteria_parts = []
            if category:
                criteria_parts.append(f"category '{category}'")
            if product_name:
                criteria_parts.append(f"name containing '{product_name}'")
            if features:
                criteria_parts.append(f"features: {', '.join(features)}")
            if max_price:
                criteria_parts.append(f"under ${max_price:.2f}")
            if min_price:
                criteria_parts.append(f"over ${min_price:.2f}")
            
            criteria_str = ", ".join(criteria_parts) if criteria_parts else "your criteria"
            
            return (f"I couldn't find products matching {criteria_str}.\n\n"
                    "Try:\n"
                    "  • Broadening your search criteria\n"
                    "  • Checking a different category\n"
                    "  • Adjusting your price range")
        
        products = products[:10]
        
        header_parts = []
        if category:
            header_parts.append(f"in {category}")
        if product_name:
            header_parts.append(f"matching '{product_name}'")
        if features:
            header_parts.append(f"with {', '.join(features)}")
        if max_price:
            header_parts.append(f"under ${max_price:.2f}")
        if min_price:
            header_parts.append(f"over ${min_price:.2f}")
        
        header = "Product Recommendations"
        if header_parts:
            header += f" ({' '.join(header_parts)})"
        header += ":\n\n"
        
        response = header
        for i, product in enumerate(products, 1):
            response += f"{i}. {product['name']} - ${product['price']:.2f}\n"
            response += f"   Category: {product['category']}\n"
            
            if product.get('features'):
                feature_list = product['features']
                if isinstance(feature_list, list) and feature_list:
                    response += f"   Features: {', '.join(feature_list[:3])}\n"
            
            if product['stock'] > 0:
                response += f"   ✅ In Stock ({product['stock']} available)\n"
            else:
                response += f"   ❌ Out of Stock\n"
            response += "\n"
        
        return response
    
    # No specific filters - use hybrid recommendations (10 items: 5 content + 5 personalized)
    recommendations = kb.get_hybrid_recommendations(user_id=user_id, total_limit=10)
    combined = recommendations['combined']
    
    if not combined:
        return ("I couldn't find any product recommendations at this time.\n\n"
                "Try:\n"
                "  • Searching for a specific category\n"
                "  • Specifying a price range\n"
                "  • Looking for specific features")
    
    # Build response with sections
    response = "🛍️ Product Recommendations:\n\n"
    
    # Separate personalized and content-based for display
    personalized = [p for p in combined if p.get('source') == 'personalized']
    content_based = [p for p in combined if p.get('source') in ['content_based', 'fallback']]
    
    item_num = 1
    
    # Show personalized recommendations first (if user is logged in)
    if personalized:
        response += "📌 Personalized for You (based on your orders):\n"
        for product in personalized:
            response += f"{item_num}. {product['name']} - ${product['price']:.2f}\n"
            response += f"   Category: {product['category']}\n"
            if product['stock'] > 0:
                response += f"   ✅ In Stock\n"
            else:
                response += f"   ❌ Out of Stock\n"
            response += "\n"
            item_num += 1
    
    # Show trending/popular products
    if content_based:
        response += "🔥 Trending Products (most popular):\n"
        for product in content_based:
            response += f"{item_num}. {product['name']} - ${product['price']:.2f}\n"
            response += f"   Category: {product['category']}\n"
            if product['stock'] > 0:
                response += f"   ✅ In Stock\n"
            else:
                response += f"   ❌ Out of Stock\n"
            response += "\n"
            item_num += 1
    
    if user_id is None:
        response += "💡 Tip: Log in to get personalized recommendations based on your orders!"
    
    return response


def handle_product_info(perception):
    
    product_id = perception.get('product_id')
    product_name = perception.get('product_name')
    
    # Try to find product by ID first
    if product_id:
        product = kb.get_product(product_id)
        if product:
            return _format_product_details(product)
    
    # If no product_id or not found, try searching by name
    if product_name:
        products = kb.search_products_advanced(name=product_name)
        if products:
            if len(products) == 1:
                return _format_product_details(products[0])
            else:
                # Multiple matches - show list
                response = f"I found {len(products)} products matching '{product_name}':\n\n"
                for i, p in enumerate(products[:5], 1):
                    response += f"{i}. {p['name']} ({p['id']}) - ${p['price']:.2f}\n"
                response += "\nPlease specify a product ID for more details."
                return response
    
    return ("I couldn't find that product.\n\n"
            "Please provide a product ID (format: P001) or product name.")


def _format_product_details(product):
    """Format product details for display."""
    response = f"📦 {product['name']}\n\n"
    response += f"Product ID: {product['id']}\n"
    response += f"Price: ${product['price']:.2f}\n"
    response += f"Category: {product['category']}\n"
    
    # Show features if available
    if product.get('features'):
        features = product['features']
        if isinstance(features, list) and features:
            response += f"Features: {', '.join(features)}\n"
    
    # Stock status
    if product['stock'] > 0:
        response += f"Stock: ✅ {product['stock']} available\n"
    else:
        response += f"Stock: ❌ Out of Stock\n"
    
    # Return policy
    if product.get('returnable'):
        response += f"Returns: ✅ Returnable within {product.get('return_window', 30)} days\n"
    else:
        response += f"Returns: ❌ Non-returnable\n"
    
    return response


def handle_shipping_policy(perception):
    """Provide shipping policy information."""
    policy = kb.get_shipping_policy()
    
    if not policy:
        return "Shipping policy information is currently unavailable."
    
    response = " Shipping Options:\n\n"
    for method, details in policy.items():
        response += f"{method.title()}:\n"
        response += f"  Duration: {details.get('duration', 'N/A')}\n"
        response += f"  Cost: {details.get('cost', 'N/A')}\n\n"
    
    return response


def handle_general_help(perception):
    return ("👋 Welcome to E-Shop Customer Support!\n\n"
            "I can help you with:\n"
            "  • Order status and tracking\n"
            "  • Return policy and procedures\n"
            "  • Product recommendations\n"
            "  • Shipping information\n\n"
            "What would you like to know?")


def handle_greet(perception):
    """Greet the user."""
    return ("👋 Hello! Welcome to E-Shop Customer Support.\n\n"
            "I'm your AI assistant. How can I assist you today?")


def handle_warranty_info(perception):
    warranty = kb.get_warranty_policy()
    
    if not warranty:
        return "Warranty information is currently unavailable."
    
    response = "Warranty Information:\n\n"
    for category, info in warranty.items():
        response += f"{category.replace('_', ' ').title()}: {info}\n"
    
    return response


def handle_payment_info(perception):
    """Provide payment information."""
    faq = kb.get_faq()
    payment_info = faq.get('payment_methods', 'Payment information not available')
    return f"💳 Payment Methods:\n\n{payment_info}"


def handle_cancellation(perception):
    """Handle order cancellation request."""
    order_id = perception.get('order_id')
    
    if order_id:
        order = kb.get_order(order_id)
        if order:
            if order['status'] == 'Processing':
                return f"I can help you cancel order {order_id}. Please contact support@eshop.com."
            elif order['status'] == 'Shipped':
                return f"Order {order_id} has already shipped. You can refuse delivery or initiate a return."
            elif order['status'] == 'Delivered':
                return f"Order {order_id} has been delivered. Please initiate a return if needed."
            else:
                return f"Order {order_id} is already {order['status'].lower()}."
        else:
            return f"I couldn't find order {order_id}."
    else:
        return "To cancel an order, please provide your order number (format: ORD12345)."


def handle_order_history(perception):
    """
    Handle order history queries with AI NLP.
    
    Supports natural language queries like:
    - "what did I order last week"
    - "show my orders"
    - "my order history"
    - "what have I purchased"
    
    Enforces authentication requirement - user must be logged in.
    Queries database filtered by user_id.
    
    Requirements: 3.1, 3.2, 3.4
    """
    user_context = perception.get('user_context', {'role': 'guest'})
    user_id = user_context.get('user_id')
    
    # Enforce authentication requirement (Requirement 3.4)
    if user_id is None:
        return ("🔒 Please log in to view your order history.\n\n"
                "Once logged in, you can ask me:\n"
                "  • 'Show my orders'\n"
                "  • 'What did I order recently?'\n"
                "  • 'My order history'")
    
    # Query orders from database filtered by user_id (Requirement 3.2)
    orders = kb.get_user_orders(user_id)
    
    if orders is None:
        return ("🔒 Please log in to view your order history.\n\n"
                "Once logged in, you can ask me:\n"
                "  • 'Show my orders'\n"
                "  • 'What did I order recently?'\n"
                "  • 'My order history'")
    
    if not orders:
        return ("📦 You don't have any orders yet.\n\n"
                "Start shopping and your order history will appear here!")
    
    # Format order history response
    response = f"📦 Your Order History ({len(orders)} order{'s' if len(orders) != 1 else ''}):\n\n"
    
    for i, order in enumerate(orders, 1):
        # Get product details for each order
        product = kb.get_product(order['product_id'])
        product_name = product['name'] if product else order['product_id']
        
        response += f"{i}. Order {order['id']}\n"
        response += f"   Product: {product_name}\n"
        response += f"   Status: {order['status']}\n"
        response += f"   Date: {order['order_date']}\n"
        response += f"   Total: ${order['total']:.2f}\n"
        
        # Add status indicator
        if order['status'] == 'Processing':
            response += "   📋 Being prepared\n"
        elif order['status'] == 'Shipped':
            response += f"   🚚 On the way (Delivery: {order['delivery_date']})\n"
        elif order['status'] == 'Delivered':
            response += "   ✅ Delivered\n"
        elif order['status'] == 'Cancelled':
            response += "   ❌ Cancelled\n"
        
        response += "\n"
    
    response += "Need details on a specific order? Just provide the order number!"
    
    return response


def handle_user_profile(perception):
    """
    Handle user profile queries with AI NLP.
    
    Supports natural language queries like:
    - "show my profile"
    - "what's my account info"
    - "my account details"
    
    Enforces authentication requirement - user must be logged in.
    Queries database for user profile.
    
    Requirements: 9.1, 9.2, 9.3
    """
    user_context = perception.get('user_context', {'role': 'guest'})
    user_id = user_context.get('user_id')
    
    # Enforce authentication requirement (Requirement 9.3)
    if user_id is None:
        return ("🔒 Please log in to view your profile.\n\n"
                "Once logged in, you can ask me:\n"
                "  • 'Show my profile'\n"
                "  • 'What's my account info?'\n"
                "  • 'My account details'")
    
    # Query user profile from database (Requirement 9.2)
    profile = kb.get_user_profile(user_id)
    
    if profile is None:
        return ("🔒 Please log in to view your profile.\n\n"
                "Once logged in, you can ask me:\n"
                "  • 'Show my profile'\n"
                "  • 'What's my account info?'\n"
                "  • 'My account details'")
    
    # Format profile response
    response = "👤 Your Profile\n\n"
    response += f"Name: {profile['name']}\n"
    response += f"Email: {profile['email']}\n"
    response += f"Account Type: {profile['role'].title()}\n"
    
    if profile.get('created_at'):
        response += f"Member Since: {profile['created_at'][:10]}\n"
    
    if profile.get('last_login'):
        response += f"Last Login: {profile['last_login'][:10]}\n"
    
    response += "\nNeed to update your information? Contact support@eshop.com"
    
    return response


@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')
        
        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Check if user is authenticated (optional)
        user_id, user_role = get_current_user_from_token()
        
        # Build user context for role-based processing
        user_context = {
            'user_id': user_id,
            'role': user_role if user_role else 'guest'
        }
        
        # Get or create conversation context for this session
        context_key = f"{user_id or 'guest'}_{session_id}"
        if context_key not in conversation_contexts:
            conversation_contexts[context_key] = ConversationContext()
            # Set auth state if authenticated
            if user_id:
                conversation_contexts[context_key].set_auth_state(user_context)
        
        conversation_context = conversation_contexts[context_key]
        
        # Process message with user context and conversation context
        response = process_message(
            message, 
            user_context=user_context,
            conversation_context=conversation_context
        )
        
        # Save messages to database for authenticated users
        if user_id:
            # Save user message
            db.save_chat_message(user_id, message, is_bot=False)
            # Save bot response
            db.save_chat_message(user_id, response, is_bot=True)
        
        return jsonify({'response': response})
    
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """
    Return server and database health status.
    
    Response: {"status": "healthy/unhealthy", "database": "connected/disconnected"}
    
    Implements: Requirements 4.3
    """
    db_connected = db.is_connected() if db else False
    
    status = {
        'status': 'healthy' if db_connected else 'unhealthy',
        'database': 'connected' if db_connected else 'disconnected'
    }
    
    status_code = 200 if db_connected else 503
    return jsonify(status), status_code


# Authentication helper functions

def hash_password(password):
    
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password, password_hash):
   
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def generate_token(user_id, role):
    
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token):
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def token_required(f):
    """
    Decorator to require valid JWT token for endpoint.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Authentication token is required'}), 401
        
        payload = decode_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Add user info to request context
        request.user_id = payload.get('user_id')
        request.user_role = payload.get('role')
        
        return f(*args, **kwargs)
    return decorated


def get_current_user_from_token():
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        payload = decode_token(token)
        if payload:
            return payload.get('user_id'), payload.get('role')
    return None, None


# Authentication endpoints

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        
        # Validate required fields
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        
        # Validate email format (basic check)
        if '@' not in email or '.' not in email:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password length
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Check if user already exists
        existing_user = db.get_user_by_email(email)
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 409
        
        # Hash password and create user (default role is 'customer')
        password_hash = hash_password(password)
        user = db.create_user(email, password_hash, name, role='customer')
        
        if not user:
            return jsonify({'error': 'Failed to create user'}), 500
        
        # Generate token
        token = generate_token(user['id'], user['role'])
        
        # Update last login
        db.update_last_login(user['id'])
        
        return jsonify({
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'role': user['role']
            },
            'token': token
        }), 201
    
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            # Generic error message - doesn't reveal which field is wrong
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Get user by email
        user = db.get_user_by_email(email)
        
        if not user:
            # Generic error message - doesn't reveal that email doesn't exist
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            # Generic error message - doesn't reveal that password is wrong
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Update last login timestamp
        db.update_last_login(user['id'])
        
        # Generate token
        token = generate_token(user['id'], user['role'])
        
        return jsonify({
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'role': user['role']
            },
            'token': token
        })
    
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/auth/logout', methods=['POST'])
@token_required
def logout():
    # JWT tokens are stateless, so logout is handled client-side
    # by discarding the token. This endpoint confirms the action.
    return jsonify({'message': 'Logged out successfully'})


@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user():
    try:
        user = db.get_user_by_id(request.user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'role': user['role']
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# Chat history endpoints

@app.route('/api/history', methods=['GET'])
@token_required
def get_chat_history():
    """
    Get chat history for authenticated user.
    
    Query params:
        limit: Maximum number of messages to return (default: 50)
    
    Response: {"messages": [...]}
    
    Implements: Requirements 6.1
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        # Cap limit to reasonable maximum
        limit = min(limit, 100)
        
        messages = db.get_chat_history(request.user_id, limit=limit)
        
        # Format messages for frontend
        formatted_messages = [
            {
                'id': msg['id'],
                'message': msg['message'],
                'is_bot': msg['is_bot'],
                'created_at': msg['created_at'].isoformat() if msg['created_at'] else None
            }
            for msg in messages
        ]
        
        return jsonify({'messages': formatted_messages})
    
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/interactions', methods=['POST'])
@token_required
def record_product_interaction():
    """
    Record a user interaction with a product.
    
    Request body: {"product_id": "P001", "interaction_type": "click"}
    Response: {"success": true}
    
    Valid interaction types: click, like, share, view, wishlist
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        product_id = data.get('product_id', '').strip()
        interaction_type = data.get('interaction_type', '').strip().lower()
        
        if not product_id:
            return jsonify({'error': 'Product ID is required'}), 400
        
        valid_types = ['click', 'like', 'share', 'view', 'wishlist']
        if interaction_type not in valid_types:
            return jsonify({'error': f'Invalid interaction type. Must be one of: {", ".join(valid_types)}'}), 400
        
        # Verify product exists
        product = kb.get_product(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Record the interaction
        success = kb.record_interaction(request.user_id, product_id, interaction_type)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to record interaction'}), 500
    
    except Exception as e:
        logger.error(f"Error recording interaction: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    """
    Get product recommendations.
    
    For authenticated users: Returns 5 personalized + 5 content-based recommendations.
    For guests: Returns 10 content-based (most clicked) recommendations.
    
    Response: {"recommendations": [...], "personalized_count": n, "content_based_count": n}
    """
    try:
        user_id, _ = get_current_user_from_token()
        
        recommendations = kb.get_hybrid_recommendations(user_id=user_id, total_limit=10)
        combined = recommendations['combined']
        
        # Format response
        formatted = []
        for product in combined:
            formatted.append({
                'id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'category': product['category'],
                'features': product.get('features', []),
                'stock': product['stock'],
                'source': product.get('source', 'unknown')
            })
        
        return jsonify({
            'recommendations': formatted,
            'personalized_count': len(recommendations['personalized']),
            'content_based_count': len(recommendations['content_based']),
            'is_authenticated': user_id is not None
        })
    
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return jsonify({'error': 'Internal server error'}), 500


def shutdown():
    global db
    if db:
        db.disconnect()
        logger.info("Database connection closed on shutdown")


if __name__ == '__main__':
    try:
        init_app()
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        shutdown()
    except Exception as e:
        logger.error(f"Failed to start API: {e}")
        shutdown()
