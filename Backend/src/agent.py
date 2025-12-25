"""
Intelligent Agent Module
Implements autonomous customer support agent
Demonstrates: Intelligent Agents
"""

from src.knowledge_base import KnowledgeBase
from src.inference_engine import InferenceEngine
from src.nlp_processor import NLPProcessor

class CustomerSupportAgent:
    """
    Intelligent agent for customer support.
    
    Agent Architecture:
    - Perception: Process user input (NLP)
    - Reasoning: Use inference engine to select action
    - Action: Execute action and generate response
    - Learning: Maintain conversation context
    """
    
    def __init__(self, data_dir='data'):
        # Initialize components
        self.kb = KnowledgeBase(data_dir)
        self.inference_engine = InferenceEngine(self.kb)
        self.nlp = NLPProcessor()
        
        # Conversation state
        self.conversation_history = []
        self.current_context = {}
    
    def perceive(self, user_input):
        """
        Perception: Process and understand user input.
        
        Args:
            user_input (str): Raw user input
            
        Returns:
            dict: Perception containing intent and entities
        """
        # Preprocess text
        processed_text = self.nlp.preprocess_text(user_input)
        
        # Classify intent
        intent = self.nlp.classify_intent(processed_text)
        
        # Extract entities
        entities = self.nlp.extract_entities(processed_text)
        
        # Create perception
        perception = {
            'intent': intent,
            'raw_input': user_input,
            'processed_input': processed_text,
            **entities
        }
        
        return perception
    
    def reason(self, perception):
        """
        Reasoning: Use inference engine to determine action.
        
        Args:
            perception (dict): Perception from user input
            
        Returns:
            dict: Selected rule/action
        """
        # Use inference engine with forward chaining
        selected_rule = self.inference_engine.infer(perception)
        
        return selected_rule
    
    def act(self, rule, perception):
        """
        Action: Execute the action and generate response.
        
        Args:
            rule (dict): Selected rule
            perception (dict): Current perception
            
        Returns:
            str: Response to user
        """
        if not rule:
            return self._handle_unknown()
        
        action = rule['action']
        
        # Execute action based on rule
        action_methods = {
            'get_order_status': self._get_order_status,
            'request_order_id': self._request_order_id,
            'get_return_policy': self._get_return_policy,
            'check_product_returnability': self._check_product_returnability,
            'recommend_products': self._recommend_products,
            'get_product_info': self._get_product_info,
            'get_shipping_policy': self._get_shipping_policy,
            'provide_general_help': self._provide_general_help,
            'greet_user': self._greet_user,
            'get_warranty_info': self._get_warranty_info,
            'get_payment_info': self._get_payment_info,
            'handle_cancellation': self._handle_cancellation,
            'search_products_advanced': self._search_products_advanced,
            'get_order_history': self._get_order_history,
            'get_user_profile': self._get_user_profile
        }
        
        action_method = action_methods.get(action, self._handle_unknown)
        return action_method(perception)
    
    # Action implementations
    
    def _get_order_status(self, perception):
        """Get order status from knowledge base"""
        order_id = perception.get('order_id')
        order = self.kb.get_order(order_id)
        
        if order:
            product = self.kb.get_product(order['product_id'])
            product_name = product['name'] if product else "your item"
            
            response = f"📦 Order Status for {order_id}:\n\n"
            response += f"Product: {product_name}\n"
            response += f"Status: {order['status']}\n"
            response += f"Order Date: {order['order_date']}\n"
            
            if order['status'] != 'Cancelled':
                response += f"Expected Delivery: {order['delivery_date']}\n"
                if order.get('tracking_number'):
                    response += f"Tracking Number: {order['tracking_number']}\n"
            
            response += f"Total: ${order['total']:.2f}"
            
            return response
        else:
            return f"❌ I couldn't find order {order_id}. Please check the order number and try again. Order numbers are in the format ORD12345."
    
    def _request_order_id(self, perception):
        """Request order ID from user"""
        return "I'd be happy to check your order status! 📦\n\nPlease provide your order number (format: ORD12345)."
    
    def _get_return_policy(self, perception):
        """Provide general return policy"""
        policy = self.kb.get_return_policy()
        
        response = "🔄 Return Policy:\n\n"
        response += f"{policy['general']}\n\n"
        response += "Conditions:\n"
        for condition in policy['conditions']:
            response += f"  • {condition}\n"
        
        response += "\nNon-returnable items:\n"
        for category in policy['non_returnable_categories']:
            response += f"  • {category}\n"
        
        response += "\nReturn Process:\n"
        for i, step in enumerate(policy['process'], 1):
            response += f"  {i}. {step}\n"
        
        return response
    
    def _check_product_returnability(self, perception):
        """Check if specific product is returnable"""
        product_id = perception.get('product_id')
        product = self.kb.get_product(product_id)
        
        if product:
            if product['returnable']:
                return f"✅ {product['name']} is returnable within {product['return_window']} days of delivery.\n\nPlease ensure the item is unused and in original packaging."
            else:
                return f"❌ {product['name']} is non-returnable as it falls under our non-returnable categories (personalized items, gift cards, etc.)."
        else:
            return self._get_return_policy(perception)
    
    def _recommend_products(self, perception):
        """Recommend products based on criteria"""
        category = perception.get('category')
        max_price = perception.get('max_price')
        
        # Search products
        products = self.kb.search_products(category=category, max_price=max_price)
        
        if not products:
            return "I couldn't find products matching your criteria. Could you provide more details about what you're looking for?"
        
        # Limit to top 5 recommendations
        products = products[:5]
        
        response = "🛍️ Product Recommendations:\n\n"
        for i, product in enumerate(products, 1):
            response += f"{i}. {product['name']} - ${product['price']:.2f}\n"
            response += f"   Category: {product['category']}\n"
            response += f"   Features: {', '.join(product['features'][:3])}\n"
            if product['stock'] > 0:
                response += f"   ✅ In Stock ({product['stock']} available)\n"
            else:
                response += f"   ❌ Out of Stock\n"
            response += "\n"
        
        return response
    
    def _get_product_info(self, perception):
        """Get detailed product information"""
        product_id = perception.get('product_id')
        product = self.kb.get_product(product_id)
        
        if product:
            response = f"📱 {product['name']}\n\n"
            response += f"Price: ${product['price']:.2f}\n"
            response += f"Category: {product['category']}\n"
            response += f"\nFeatures:\n"
            for feature in product['features']:
                response += f"  • {feature}\n"
            response += f"\nStock: {product['stock']} available\n"
            response += f"Returnable: {'Yes' if product['returnable'] else 'No'}\n"
            return response
        else:
            return "I couldn't find that product. Please check the product ID or describe what you're looking for."
    
    def _get_shipping_policy(self, perception):
        """Provide shipping policy information"""
        policy = self.kb.get_shipping_policy()
        
        response = "🚚 Shipping Options:\n\n"
        for method, details in policy.items():
            response += f"{method.title()}:\n"
            response += f"  Duration: {details['duration']}\n"
            response += f"  Cost: {details['cost']}\n\n"
        
        return response
    
    def _provide_general_help(self, perception):
        """Provide general help information"""
        return ("👋 Welcome to E-Shop Customer Support!\n\n"
                "I can help you with:\n"
                "  • Order status and tracking\n"
                "  • Return policy and procedures\n"
                "  • Product recommendations\n"
                "  • Shipping information\n"
                "  • Payment methods\n"
                "  • Warranty information\n\n"
                "What would you like to know?")
    
    def _greet_user(self, perception):
        """Greet the user"""
        return ("👋 Hello! Welcome to E-Shop Customer Support.\n\n"
                "I'm your AI assistant, here to help with orders, returns, "
                "product recommendations, and more. How can I assist you today?")
    
    def _get_warranty_info(self, perception):
        """Provide warranty information"""
        warranty = self.kb.get_warranty_policy()
        
        response = "🛡️ Warranty Information:\n\n"
        for category, info in warranty.items():
            response += f"{category.replace('_', ' ').title()}: {info}\n"
        
        return response
    
    def _get_payment_info(self, perception):
        """Provide payment information"""
        faq = self.kb.get_faq()
        payment_info = faq.get('payment_methods', 'Payment information not available')
        
        return f"💳 Payment Methods:\n\n{payment_info}"
    
    def _handle_cancellation(self, perception):
        """Handle order cancellation request"""
        order_id = perception.get('order_id')
        
        if order_id:
            order = self.kb.get_order(order_id)
            if order:
                if order['status'] == 'Processing':
                    return f"I can help you cancel order {order_id}. Since it's still processing, we can cancel it. Please contact our support team at support@eshop.com or call 1-800-ESHOP to complete the cancellation."
                elif order['status'] == 'Shipped':
                    return f"Order {order_id} has already shipped. You can refuse delivery or initiate a return once you receive it."
                elif order['status'] == 'Delivered':
                    return f"Order {order_id} has been delivered. Please initiate a return if you'd like to send it back."
                else:
                    return f"Order {order_id} is already {order['status'].lower()}."
            else:
                return f"I couldn't find order {order_id}. Please check the order number."
        else:
            return "To cancel an order, please provide your order number (format: ORD12345)."
    
    def _search_products_advanced(self, perception):
        """Search products by name, feature, or category"""
        # Extract search terms from the processed input
        search_text = perception.get('processed_input', '')
        category = perception.get('category')
        
        # Try to extract a product name from the search text
        # Remove common search words
        search_words = ['search', 'find', 'show', 'products', 'product', 'with', 'for', 'me', 'a', 'an', 'the']
        words = search_text.lower().split()
        name_words = [w for w in words if w not in search_words]
        name_search = ' '.join(name_words) if name_words else None
        
        # Search using the advanced method
        products = self.kb.search_products_advanced(
            name=name_search,
            category=category
        )
        
        if not products:
            return f"🔍 No products found matching '{name_search or search_text}'. Try different search terms or browse by category."
        
        response = f"🔍 Search Results for '{name_search or search_text}':\n\n"
        for i, product in enumerate(products, 1):
            response += f"{i}. {product['name']} - ${product['price']:.2f}\n"
            response += f"   Category: {product['category']}\n"
            if product['features']:
                response += f"   Features: {', '.join(product['features'][:3])}\n"
            if product['stock'] > 0:
                response += f"   ✅ In Stock ({product['stock']} available)\n"
            else:
                response += f"   ❌ Out of Stock\n"
            response += "\n"
        
        return response
    
    def _get_order_history(self, perception):
        """Get order history for authenticated user"""
        user_id = perception.get('user_id')
        
        if not user_id:
            return "🔒 Please log in to view your order history."
        
        orders = self.kb.get_user_orders(user_id)
        
        if orders is None:
            return "🔒 Please log in to view your order history."
        
        if not orders:
            return "📦 You don't have any orders yet. Start shopping to see your order history here!"
        
        response = "📦 Your Order History:\n\n"
        for order in orders:
            product = self.kb.get_product(order['product_id'])
            product_name = product['name'] if product else order['product_id']
            
            response += f"Order {order['id']}:\n"
            response += f"  Product: {product_name}\n"
            response += f"  Status: {order['status']}\n"
            response += f"  Date: {order['order_date']}\n"
            response += f"  Total: ${order['total']:.2f}\n\n"
        
        return response
    
    def _get_user_profile(self, perception):
        """Get user profile information"""
        user_id = perception.get('user_id')
        
        if not user_id:
            return "🔒 Please log in to view your profile."
        
        profile = self.kb.get_user_profile(user_id)
        
        if not profile:
            return "🔒 Please log in to view your profile."
        
        response = "👤 Your Profile:\n\n"
        response += f"Name: {profile['name']}\n"
        response += f"Email: {profile['email']}\n"
        response += f"Role: {profile['role'].title()}\n"
        response += f"Member Since: {profile['created_at']}\n"
        if profile['last_login']:
            response += f"Last Login: {profile['last_login']}\n"
        
        return response
    
    def _handle_unknown(self):
        """Handle unknown intent or action"""
        return ("I'm ai assistant for your service. 🤔\n\n"
                "I can help you with:\n"
                "  • Order status (provide order number)\n"
                "  • Return policy\n"
                "  • Product recommendations\n"
                "  • General inquiries\n\n"
                "Could you please rephrase your question?")
    
    def run(self, user_input):
        # Perception phase
        perception = self.perceive(user_input)
        
        # Reasoning phase
        rule = self.reason(perception)
        
        # Action phase
        response = self.act(rule, perception)
        
        # Update conversation history (learning/context)
        self.conversation_history.append({
            'user': user_input,
            'bot': response,
            'intent': perception['intent'],
            'rule_id': rule['id'] if rule else None
        })
        
        # Update context
        self.current_context = perception
        
        return response
    
    def get_conversation_history(self):
        """Get conversation history"""
        return self.conversation_history
    
    def reset(self):
        """Reset agent state"""
        self.conversation_history = []
        self.current_context = {}
        self.kb.clear_facts()
