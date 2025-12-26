

import logging
import re
from typing import Dict, Any, Optional, List

from .nlp_config import NLPConfig, default_config
from .nlp_processor import NLPProcessor

logger = logging.getLogger(__name__)


class AINLPProcessor:
    
    
    # Mapping from zero-shot labels to internal intent names
    INTENT_MAPPING = {
        "greeting": "greeting",
        "order status inquiry": "order_status",
        "order history request": "order_history",
        "return policy question": "return_policy",
        "product recommendation request": "product_recommendation",
        "product search": "product_search",
        "product information request": "product_info",
        "shipping information": "shipping_info",
        "warranty information": "warranty_info",
        "payment information": "payment_info",
        "order cancellation": "cancel_order",
        "user profile request": "user_profile",
        "general help": "general_inquiry"
    }
    
    def __init__(self, config: Optional[NLPConfig] = None):
        
        self.config = config or NLPConfig.from_env()
        self.use_ai = False
        self.classifier = None
        self.fallback_nlp = NLPProcessor()
        
        self._load_model()
    
    def _load_model(self) -> None:
        
        try:
            from transformers import pipeline
            
            logger.info(f"Loading AI model: {self.config.model_name}")
            self.classifier = pipeline(
                "zero-shot-classification",
                model=self.config.model_name
            )
            self.use_ai = True
            logger.info("AI model loaded successfully")
            
        except ImportError as e:
            logger.error(f"Transformers library not available: {e}")
            self.use_ai = False
            
        except Exception as e:
            logger.error(f"Failed to load AI model: {e}")
            self.use_ai = False
    
    def _map_intent(self, label: str) -> str:
        
        return self.INTENT_MAPPING.get(label, "general_inquiry")

    def classify_intent(self, text: str) -> Dict[str, Any]:
        
        if not text or not text.strip():
            return {
                'intent': 'general_inquiry',
                'confidence': 0.0,
                'all_scores': {},
                'used_fallback': True,
                'is_ambiguous': False,
                'ambiguous_intents': [],
                'needs_clarification': False
            }
        
        # Try AI classification if available
        if self.use_ai and self.classifier is not None:
            try:
                result = self._classify_with_ai(text)
                
                # Check for ambiguity (top intents have similar scores)
                ambiguity_result = self._check_ambiguity(result)
                result.update(ambiguity_result)
                
                # Check if confidence meets threshold
                if result['confidence'] >= self.config.confidence_threshold:
                    return result
                else:
                    # Confidence too low, use fallback
                    logger.debug(
                        f"AI confidence {result['confidence']:.2f} below threshold "
                        f"{self.config.confidence_threshold}, using fallback"
                    )
                    fallback_result = self._classify_with_fallback(text)
                    fallback_result['all_scores'] = result['all_scores']
                    # Mark as needing clarification due to low confidence
                    fallback_result['needs_clarification'] = True
                    return fallback_result
                    
            except Exception as e:
                logger.error(f"AI classification failed: {e}")
                return self._classify_with_fallback(text)
        
        # AI not available, use fallback
        return self._classify_with_fallback(text)
    
    def _classify_with_ai(self, text: str) -> Dict[str, Any]:
        
        result = self.classifier(
            text,
            candidate_labels=self.config.intent_labels,
            multi_label=False
        )
        
        # Build all_scores dictionary
        all_scores = {}
        for label, score in zip(result['labels'], result['scores']):
            mapped_intent = self._map_intent(label)
            all_scores[mapped_intent] = score
        
        # Get top intent
        top_label = result['labels'][0]
        top_score = result['scores'][0]
        mapped_intent = self._map_intent(top_label)
        
        return {
            'intent': mapped_intent,
            'confidence': float(top_score),
            'all_scores': all_scores,
            'used_fallback': False,
            'is_ambiguous': False,
            'ambiguous_intents': [],
            'needs_clarification': False
        }
    
    def _check_ambiguity(self, classification_result: Dict[str, Any]) -> Dict[str, Any]:
        
        all_scores = classification_result.get('all_scores', {})
        
        if len(all_scores) < 2:
            return {
                'is_ambiguous': False,
                'ambiguous_intents': [],
                'needs_clarification': False
            }
        
        # Sort intents by score descending
        sorted_intents = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
        
        top_intent, top_score = sorted_intents[0]
        second_intent, second_score = sorted_intents[1]
        
        # Check if scores are within ambiguity threshold
        score_difference = top_score - second_score
        
        if score_difference < self.config.ambiguity_threshold:
            # Ambiguous - top intents have similar scores
            ambiguous_intents = [
                {'intent': top_intent, 'score': top_score},
                {'intent': second_intent, 'score': second_score}
            ]
            
            # Check if there's a third intent also close
            if len(sorted_intents) > 2:
                third_intent, third_score = sorted_intents[2]
                if top_score - third_score < self.config.ambiguity_threshold * 2:
                    ambiguous_intents.append({'intent': third_intent, 'score': third_score})
            
            logger.debug(
                f"Ambiguous intent detected: {top_intent} ({top_score:.2f}) vs "
                f"{second_intent} ({second_score:.2f}), diff={score_difference:.2f}"
            )
            
            return {
                'is_ambiguous': True,
                'ambiguous_intents': ambiguous_intents,
                'needs_clarification': True
            }
        
        return {
            'is_ambiguous': False,
            'ambiguous_intents': [],
            'needs_clarification': False
        }
    
    def _classify_with_fallback(self, text: str) -> Dict[str, Any]:
        
        intent = self.fallback_nlp.classify_intent(text)
        
        return {
            'intent': intent,
            'confidence': 0.5,  # Default confidence for keyword matching
            'all_scores': {intent: 0.5},
            'used_fallback': True,
            'is_ambiguous': False,
            'ambiguous_intents': [],
            'needs_clarification': False
        }

    # Category keywords for entity extraction
    CATEGORY_KEYWORDS = {
        'electronics': ['electronic', 'electronics', 'gadget', 'gadgets', 'device', 
                       'devices', 'tech', 'technology', 'phone', 'laptop', 'computer',
                       'tablet', 'headphone', 'headphones', 'speaker', 'speakers',
                       'camera', 'tv', 'television', 'monitor', 'keyboard', 'mouse'],
        'sports': ['sport', 'sports', 'fitness', 'exercise', 'workout', 'athletic',
                  'gym', 'running', 'yoga', 'basketball', 'football', 'soccer',
                  'tennis', 'golf', 'swimming', 'cycling', 'bike'],
        'home': ['home', 'house', 'kitchen', 'living', 'bedroom', 'bathroom',
                'furniture', 'decor', 'appliance', 'appliances', 'cookware'],
        'accessories': ['accessory', 'accessories', 'add-on', 'addon', 'case',
                       'cover', 'charger', 'cable', 'adapter', 'mount', 'stand'],
        'clothing': ['clothing', 'clothes', 'shirt', 'pants', 'dress', 'jacket',
                    'shoes', 'hat', 'socks', 'underwear', 'coat', 'sweater'],
        'books': ['book', 'books', 'novel', 'textbook', 'magazine', 'reading'],
        'toys': ['toy', 'toys', 'game', 'games', 'puzzle', 'lego', 'doll', 'action figure']
    }
    
    # Feature keywords for entity extraction
    FEATURE_KEYWORDS = [
        'wireless', 'bluetooth', 'wifi', 'wi-fi', 'portable', 'rechargeable',
        'waterproof', 'water-resistant', 'lightweight', 'heavy-duty', 'compact',
        'foldable', 'adjustable', 'ergonomic', 'noise-cancelling', 'noise cancelling',
        'smart', 'digital', 'analog', 'automatic', 'manual', 'premium', 'budget',
        'professional', 'beginner', 'advanced', 'mini', 'large', 'small', 'medium',
        'fast', 'quick', 'durable', 'long-lasting', 'eco-friendly', 'organic',
        'led', 'lcd', 'oled', 'hd', '4k', '1080p', 'usb', 'usb-c', 'hdmi'
    ]

    def extract_entities(self, text: str) -> Dict[str, Any]:
       
        if not text:
            return self._empty_entities()
        
        entities = {
            'order_id': None,
            'product_id': None,
            'category': None,
            'max_price': None,
            'min_price': None,
            'features': [],
            'product_name': None,
            'has_order_id': False,
            'has_product_id': False
        }
        
        # Extract order ID (ORD followed by 5 digits)
        order_id = self._extract_order_id(text)
        if order_id:
            entities['order_id'] = order_id
            entities['has_order_id'] = True
        
        # Extract product ID (P followed by 3 digits)
        product_id = self._extract_product_id(text)
        if product_id:
            entities['product_id'] = product_id
            entities['has_product_id'] = True
        
        # Extract prices
        max_price, min_price = self._extract_prices(text)
        if max_price is not None:
            entities['max_price'] = max_price
        if min_price is not None:
            entities['min_price'] = min_price
        
        # Extract category
        category = self._extract_category(text)
        if category:
            entities['category'] = category
        
        # Extract features
        features = self._extract_features(text)
        if features:
            entities['features'] = features
        
        # Extract product name
        product_name = self._extract_product_name(text)
        if product_name:
            entities['product_name'] = product_name
        
        return entities
    
    def _empty_entities(self) -> Dict[str, Any]:
        """Return empty entities dictionary."""
        return {
            'order_id': None,
            'product_id': None,
            'category': None,
            'max_price': None,
            'min_price': None,
            'features': [],
            'product_name': None,
            'has_order_id': False,
            'has_product_id': False
        }
    
    def _extract_order_id(self, text: str) -> Optional[str]:
        
        pattern = r'ORD\d{5}'
        match = re.search(pattern, text.upper())
        return match.group(0) if match else None
    
    def _extract_product_id(self, text: str) -> Optional[str]:
        """
        Extract product ID using P### pattern.
        
        Args:
            text: User message
            
        Returns:
            Product ID string or None
            
        Requirements: 10.4
        """
        pattern = r'P\d{3}'
        match = re.search(pattern, text.upper())
        return match.group(0) if match else None
    
    def _extract_prices(self, text: str) -> tuple:
        """
        Extract price information from text.
        
        Handles formats:
        - $XX or $XX.XX
        - XX dollars
        - under/below/less than $XX (max_price)
        - over/above/more than $XX (min_price)
        
        Args:
            text: User message
            
        Returns:
            Tuple of (max_price, min_price), either can be None
            
        Requirements: 10.1
        """
        text_lower = text.lower()
        max_price = None
        min_price = None
        
        # Pattern for "under/below/less than $XX" or "under/below/less than XX dollars"
        under_patterns = [
            r'(?:under|below|less than|cheaper than|max|maximum)\s*\$(\d+(?:\.\d{2})?)',
            r'(?:under|below|less than|cheaper than|max|maximum)\s*(\d+(?:\.\d{2})?)\s*dollars?'
        ]
        
        for pattern in under_patterns:
            match = re.search(pattern, text_lower)
            if match:
                max_price = float(match.group(1))
                break
        
        # Pattern for "over/above/more than $XX" or "over/above/more than XX dollars"
        over_patterns = [
            r'(?:over|above|more than|at least|min|minimum)\s*\$(\d+(?:\.\d{2})?)',
            r'(?:over|above|more than|at least|min|minimum)\s*(\d+(?:\.\d{2})?)\s*dollars?'
        ]
        
        for pattern in over_patterns:
            match = re.search(pattern, text_lower)
            if match:
                min_price = float(match.group(1))
                break
        
        # If no directional price found, look for standalone price as max_price
        if max_price is None and min_price is None:
            # $XX or $XX.XX format
            dollar_pattern = r'\$(\d+(?:\.\d{2})?)'
            match = re.search(dollar_pattern, text)
            if match:
                max_price = float(match.group(1))
            else:
                # XX dollars format
                dollars_pattern = r'(\d+(?:\.\d{2})?)\s*dollars?'
                match = re.search(dollars_pattern, text_lower)
                if match:
                    max_price = float(match.group(1))
        
        return max_price, min_price
    
    def _extract_category(self, text: str) -> Optional[str]:
        """
        Extract product category from keywords.
        
        Args:
            text: User message
            
        Returns:
            Category string or None
            
        Requirements: 10.2
        """
        text_lower = text.lower()
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                # Use word boundary matching to avoid partial matches
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_lower):
                    return category
        
        return None
    
    def _extract_features(self, text: str) -> List[str]:
        """
        Extract product features from natural language.
        
        Args:
            text: User message
            
        Returns:
            List of extracted feature strings
            
        Requirements: 10.5
        """
        text_lower = text.lower()
        found_features = []
        
        for feature in self.FEATURE_KEYWORDS:
            # Use word boundary matching
            pattern = r'\b' + re.escape(feature) + r'\b'
            if re.search(pattern, text_lower):
                # Normalize feature name (replace hyphens with spaces for consistency)
                normalized = feature.replace('-', ' ')
                if normalized not in found_features:
                    found_features.append(normalized)
        
        return found_features
    
    def _extract_product_name(self, text: str) -> Optional[str]:
        """
        Extract potential product name from text.
        
        Looks for patterns like "iPhone cases", "Samsung TV", etc.
        
        Args:
            text: User message
            
        Returns:
            Product name string or None
        """
        # Common product name patterns
        # Look for capitalized words that might be product names
        # Pattern: word starting with capital followed by optional words
        patterns = [
            r'\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z]?[a-zA-Z0-9]+)*)\s+(?:case|cover|charger|cable|accessory|accessories)',
            r'(?:looking for|find|search for|want|need)\s+(?:a\s+)?([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*)',
            r'(?:do you have|have any)\s+([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                product_name = match.group(1).strip()
                # Filter out common non-product words
                non_products = ['the', 'a', 'an', 'some', 'any', 'good', 'best', 'cheap', 'expensive']
                if product_name.lower() not in non_products and len(product_name) > 1:
                    return product_name
        
        return None
    
    def _preprocess_text(self, text: str) -> str:
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters except those in order/product IDs and prices
        # Keep alphanumeric, spaces, $, and common punctuation
        text = re.sub(r'[^\w\s\$\.\,\?\!]', '', text)
        
        return text.strip()
    
    def process(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        
        if not text:
            return {
                'intent': 'general_inquiry',
                'confidence': 0.0,
                'entities': self._empty_entities(),
                'processed_input': '',
                'raw_input': '',
                'used_fallback': True,
                'all_intent_scores': {},
                'is_ambiguous': False,
                'ambiguous_intents': [],
                'needs_clarification': False
            }
        
        # Preprocess text
        processed_text = self._preprocess_text(text)
        
        # Classify intent
        classification = self.classify_intent(processed_text)
        
        # Extract entities
        entities = self.extract_entities(text)  # Use original text for entity extraction
        
        # Apply context if available
        if context:
            entities = self._apply_context(entities, context)
        
        return {
            'intent': classification['intent'],
            'confidence': classification['confidence'],
            'entities': entities,
            'processed_input': processed_text,
            'raw_input': text,
            'used_fallback': classification['used_fallback'],
            'all_intent_scores': classification.get('all_scores', {}),
            'is_ambiguous': classification.get('is_ambiguous', False),
            'ambiguous_intents': classification.get('ambiguous_intents', []),
            'needs_clarification': classification.get('needs_clarification', False)
        }
    
    def _apply_context(self, entities: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        
        if not context:
            return entities
        
        context_entities = context.get('entities', {})
        
        # Fill in missing entities from context
        for key in ['order_id', 'product_id', 'category', 'product_name']:
            if entities.get(key) is None and context_entities.get(key) is not None:
                entities[key] = context_entities[key]
                # Update has_* flags if applicable
                if key == 'order_id':
                    entities['has_order_id'] = True
                elif key == 'product_id':
                    entities['has_product_id'] = True
        
        return entities

    # Human-readable intent descriptions for clarification questions
    INTENT_DESCRIPTIONS = {
        'order_status': 'check the status of an order',
        'order_history': 'view your order history',
        'return_policy': 'learn about our return policy',
        'product_recommendation': 'get product recommendations',
        'product_search': 'search for products',
        'product_info': 'get information about a specific product',
        'shipping_info': 'learn about shipping options',
        'warranty_info': 'learn about warranty coverage',
        'payment_info': 'learn about payment methods',
        'cancel_order': 'cancel an order',
        'user_profile': 'view your account profile',
        'greeting': 'say hello',
        'general_inquiry': 'get general help'
    }
    
    # Example queries for each intent
    INTENT_EXAMPLES = {
        'order_status': '"What\'s the status of ORD12345?"',
        'order_history': '"Show my recent orders"',
        'return_policy': '"What\'s your return policy?"',
        'product_recommendation': '"Recommend some electronics under $100"',
        'product_search': '"Find wireless headphones"',
        'product_info': '"Tell me about product P001"',
        'shipping_info': '"How long does shipping take?"',
        'warranty_info': '"What warranty do you offer?"',
        'payment_info': '"What payment methods do you accept?"',
        'cancel_order': '"I want to cancel my order"',
        'user_profile': '"Show my profile"',
        'greeting': '"Hello!"',
        'general_inquiry': '"I need help"'
    }
    
    def generate_clarification_question(self, ambiguous_intents: List[Dict[str, Any]]) -> str:
        
        if not ambiguous_intents:
            return self.generate_low_confidence_suggestions()
        
        question = "I'm not quite sure what you're looking for. Did you want to:\n\n"
        
        for i, intent_info in enumerate(ambiguous_intents, 1):
            intent = intent_info['intent']
            description = self.INTENT_DESCRIPTIONS.get(intent, f"help with {intent.replace('_', ' ')}")
            example = self.INTENT_EXAMPLES.get(intent, '')
            
            question += f"  {i}. {description.capitalize()}"
            if example:
                question += f"\n     Example: {example}"
            question += "\n"
        
        question += "\nPlease let me know which one, or rephrase your question!"
        
        return question
    
    def generate_low_confidence_suggestions(self) -> str:
        
        suggestions = "Hello... I'm AI assistant for your request.\n\n"
        suggestions += "Here are some things I can help you with:\n\n"
        suggestions += "📦 Orders:\n"
        suggestions += "  • \"What's the status of ORD12345?\"\n"
        suggestions += "  • \"Show my order history\"\n"
        suggestions += "  • \"Cancel my order ORD12345\"\n\n"
        suggestions += "🛍️ Products:\n"
        suggestions += "  • \"Recommend electronics under $100\"\n"
        suggestions += "  • \"Find wireless headphones\"\n"
        suggestions += "  • \"Tell me about product P001\"\n\n"
        suggestions += "📋 Policies:\n"
        suggestions += "  • \"What's your return policy?\"\n"
        suggestions += "  • \"How long does shipping take?\"\n"
        suggestions += "  • \"What warranty do you offer?\"\n\n"
        suggestions += "👤 Account:\n"
        suggestions += "  • \"Show my profile\"\n\n"
        suggestions += "Could you please rephrase your question?"
        
        return suggestions
