"""
NLP Processor Module
Implements natural language processing for intent classification and entity extraction
Demonstrates: Natural Language Processing (Unit 1 - Application Areas)
"""

import re

class NLPProcessor:
    """
    Simple NLP for intent classification and entity extraction.
    Uses keyword matching and regex patterns.
    """
    
    def __init__(self):
        # Intent keywords for classification
        self.intent_keywords = {
            'greeting': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'greetings'],
            'order_status': ['order', 'track', 'status', 'where', 'delivery', 'shipped', 'tracking', 'when will'],
            'return_policy': ['return', 'refund', 'exchange', 'send back', 'policy', 'money back'],
            'product_recommendation': ['recommend', 'suggest', 'looking for', 'need', 'want to buy', 'show me', 'find'],
            'product_info': ['tell me about', 'details', 'information', 'price', 'features', 'specs', 'what is'],
            'shipping_info': ['shipping', 'delivery time', 'how long', 'ship', 'deliver'],
            'warranty_info': ['warranty', 'guarantee', 'coverage', 'protection'],
            'payment_info': ['payment', 'pay', 'credit card', 'paypal', 'how to pay'],
            'cancel_order': ['cancel', 'cancellation', 'stop order', 'dont want'],
            'general_inquiry': ['help', 'support', 'question', 'info', 'tell me']
        }
    
    def classify_intent(self, text):
        """
        Classify user intent using keyword matching.
        
        Args:
            text (str): User input text
            
        Returns:
            str: Classified intent
        """
        text_lower = text.lower()
        
        # Count keyword matches for each intent
        scores = {}
        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[intent] = score
        
        # Return intent with highest score
        max_score = max(scores.values())
        if max_score > 0:
            return max(scores, key=scores.get)
        
        return 'general_inquiry'
    
    def extract_order_id(self, text):
        """
        Extract order ID using regex pattern.
        Pattern: ORD followed by 5 digits
        
        Args:
            text (str): User input text
            
        Returns:
            str: Order ID or None
        """
        pattern = r'ORD\d{5}'
        match = re.search(pattern, text.upper())
        return match.group(0) if match else None
    
    def extract_product_id(self, text):
        """
        Extract product ID using regex pattern.
        Pattern: P followed by 3 digits
        
        Args:
            text (str): User input text
            
        Returns:
            str: Product ID or None
        """
        pattern = r'P\d{3}'
        match = re.search(pattern, text.upper())
        return match.group(0) if match else None
    
    def extract_price(self, text):
        """
        Extract price from text.
        Patterns: $XX, $XX.XX, XX dollars
        
        Args:
            text (str): User input text
            
        Returns:
            float: Price or None
        """
        # Pattern for $XX or $XX.XX
        pattern1 = r'\$(\d+(?:\.\d{2})?)'
        match1 = re.search(pattern1, text)
        if match1:
            return float(match1.group(1))
        
        # Pattern for XX dollars
        pattern2 = r'(\d+(?:\.\d{2})?)\s*dollars?'
        match2 = re.search(pattern2, text.lower())
        if match2:
            return float(match2.group(1))
        
        return None
    
    def extract_category(self, text):
        """
        Extract product category from text.
        
        Args:
            text (str): User input text
            
        Returns:
            str: Category or None
        """
        categories = {
            'electronics': ['electronic', 'electronics', 'gadget', 'device', 'tech'],
            'sports': ['sport', 'sports', 'fitness', 'exercise', 'workout', 'athletic'],
            'home': ['home', 'house', 'kitchen', 'living'],
            'accessories': ['accessory', 'accessories', 'add-on']
        }
        
        text_lower = text.lower()
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return None
    
    def extract_entities(self, text):
        """
        Extract all entities from text.
        
        Args:
            text (str): User input text
            
        Returns:
            dict: Extracted entities
        """
        entities = {}
        
        # Extract order ID
        order_id = self.extract_order_id(text)
        if order_id:
            entities['order_id'] = order_id
            entities['has_order_id'] = True
        else:
            entities['has_order_id'] = False
        
        # Extract product ID
        product_id = self.extract_product_id(text)
        if product_id:
            entities['product_id'] = product_id
            entities['has_product_id'] = True
        else:
            entities['has_product_id'] = False
        
        # Extract price
        price = self.extract_price(text)
        if price:
            entities['max_price'] = price
        
        # Extract category
        category = self.extract_category(text)
        if category:
            entities['category'] = category
        
        return entities
    
    def preprocess_text(self, text):
        """
        Preprocess text for better matching.
        
        Args:
            text (str): User input text
            
        Returns:
            str: Preprocessed text
        """
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters except those in order/product IDs
        # Keep alphanumeric, spaces, and common punctuation
        text = re.sub(r'[^\w\s\$\.]', '', text)
        
        return text.strip()
