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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Global database and agent components
db = None
kb = None
inference_engine = None
nlp = None


def init_app():
    """Initialize database connection and agent components."""
    global db, kb, inference_engine, nlp
    
    try:
        db = Database()
        db.connect()
        kb = KnowledgeBase(db)
        inference_engine = InferenceEngine(kb)
        nlp = NLPProcessor()
        logger.info("API initialized successfully")
    except (DatabaseConnectionError, ConfigurationError) as e:
        logger.error(f"Failed to initialize API: {e}")
        raise


def process_message(user_input, user_context=None):
    if user_context is None:
        user_context = {'user_id': None, 'role': 'guest'}
    
    # Perception phase
    processed_text = nlp.preprocess_text(user_input)
    intent = nlp.classify_intent(processed_text)
    entities = nlp.extract_entities(processed_text)
    
    perception = {
        'intent': intent,
        'raw_input': user_input,
        'processed_input': processed_text,
        'user_context': user_context,
        **entities
    }
    
    # Reasoning phase
    rule = inference_engine.infer(perception)
    
    # Action phase
    if not rule:
        return ("I'm not sure I understood that correctly.\n\n"
                "I can help you with:\n"
                "  • Order status (provide order number)\n"
                "  • Return policy\n"
                "  • Product recommendations\n"
                "  • General inquiries\n\n"
                "Could you please rephrase your question?")
    
    action = rule['action']
    response = execute_action(action, perception)
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
    
    order = kb.get_order(order_id)
    
    if order:
        # Role-based access check
        # For now, we allow all roles to view orders by ID
        # In a full implementation, orders would be linked to user_id
        # and customers would only see their own orders
        
        product = kb.get_product(order['product_id'])
        product_name = product['name'] if product else "your item"
        
        response = f"Order Status for {order_id}:\n\n"
        response += f"Product: {product_name}\n"
        response += f"Status: {order['status']}\n"
        response += f"Order Date: {order['order_date']}\n"
        
        if order['status'] != 'Cancelled':
            response += f"Expected Delivery: {order['delivery_date']}\n"
            if order.get('tracking_number'):
                response += f"Tracking Number: {order['tracking_number']}\n"
        
        response += f"Total: ${order['total']:.2f}"
        
        # Add personalized message for authenticated users
        if user_role == 'customer' and user_id:
            response += "\n\nAs a registered customer, your chat history is saved."
        elif user_role == 'admin':
            response += "\n\n Admin access: Full order details available."
        
        return response
    else:
        return f"I couldn't find order {order_id}. Please check the order number and try again."


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
    
    products = kb.search_products(category=category, max_price=max_price)
    
    if not products:
        return "I couldn't find products matching your criteria."
    
    products = products[:5]
    
    response = "Product Recommendations:\n\n"
    for i, product in enumerate(products, 1):
        response += f"{i}. {product['name']} - ${product['price']:.2f}\n"
        response += f"   Category: {product['category']}\n"
        if product['stock'] > 0:
            response += f"   ✅ In Stock\n"
        else:
            response += f"   ❌ Out of Stock\n"
        response += "\n"
    
    return response


def handle_product_info(perception):
    product_id = perception.get('product_id')
    product = kb.get_product(product_id)
    
    if product:
        response = f" {product['name']}\n\n"
        response += f"Price: ${product['price']:.2f}\n"
        response += f"Category: {product['category']}\n"
        response += f"Stock: {product['stock']} available\n"
        return response
    else:
        return "I couldn't find that product."


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


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Process chat message and return response.
    For authenticated users, stores messages in database and provides
    role-based access to information.
    
    Request body: {"message": "user message"}
    Response: {"response": "chatbot response"}
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Check if user is authenticated (optional)
        user_id, user_role = get_current_user_from_token()
        
        # Build user context for role-based processing
        user_context = {
            'user_id': user_id,
            'role': user_role if user_role else 'guest'
        }
        
        # Process message with user context
        response = process_message(message, user_context=user_context)
        
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
