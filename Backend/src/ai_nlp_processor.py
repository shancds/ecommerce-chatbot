

import logging
import re
import json
import concurrent.futures
from typing import Dict, Any, Optional, List

from .nlp_config import NLPConfig, OpenAIConfig, default_config
from .nlp_processor import NLPProcessor

logger = logging.getLogger(__name__)


class AINLPProcessor:
    
    
    
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
    
    # Reverse mapping for OpenAI model
    REVERSE_INTENT_MAPPING = {v: k for k, v in INTENT_MAPPING.items()}
    
    def __init__(self, config: Optional[NLPConfig] = None, openai_config: Optional[OpenAIConfig] = None):
        
        self.config = config or NLPConfig.from_env()
        self.openai_config = openai_config or OpenAIConfig.from_env()
        self.use_ai = False
        self.use_openai = False
        self.classifier = None
        self.openai_client = None
        self.fallback_nlp = NLPProcessor()
        
        # Weight configuration for ensemble
        self.hf_weight = 1.0 - self.openai_config.weight if self.openai_config.weight else 0.4
        self.openai_weight = self.openai_config.weight if self.openai_config.weight else 0.6
        
        self._load_model()
        self._load_openai_model()
    
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
    
    def _load_openai_model(self) -> None:
        """Load the OpenAI-compatible model (AIML API)."""
        if not self.openai_config.is_configured():
            logger.info("OpenAI model not configured or disabled")
            self.use_openai = False
            return
        
        try:
            from openai import OpenAI
            
            logger.info(f"Initializing OpenAI client with model: {self.openai_config.model_name}")
            self.openai_client = OpenAI(
                base_url=self.openai_config.api_base_url,
                api_key=self.openai_config.api_key,
                timeout=self.openai_config.timeout
            )
            self.use_openai = True
            logger.info("OpenAI client initialized successfully")
            
        except ImportError as e:
            logger.error(f"OpenAI library not available: {e}")
            self.use_openai = False
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.use_openai = False
    
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
                'needs_clarification': False,
                'model_used': 'none'
            }
        
        # Use hybrid classification if both models are available
        if self.use_ai and self.use_openai and self.classifier is not None and self.openai_client is not None:
            try:
                result = self._classify_with_hybrid(text)
                
                # Check ambiguity
                ambiguity_result = self._check_ambiguity(result)
                result.update(ambiguity_result)
                
                if result['confidence'] >= self.config.confidence_threshold:
                    return result
                else:
                    logger.debug(
                        f"Hybrid confidence {result['confidence']:.2f} below threshold "
                        f"{self.config.confidence_threshold}, using fallback"
                    )
                    fallback_result = self._classify_with_fallback(text)
                    fallback_result['all_scores'] = result['all_scores']
                    fallback_result['needs_clarification'] = True
                    return fallback_result
                    
            except Exception as e:
                logger.error(f"Hybrid classification failed: {e}")
                # Try individual models
        
        # Try HuggingFace only
        if self.use_ai and self.classifier is not None:
            try:
                result = self._classify_with_ai(text)
                
                # If HuggingFace confidence is low, try OpenAI for verification
                if result['confidence'] < self.config.confidence_threshold and self.use_openai:
                    openai_result = self._classify_with_openai(text)
                    if openai_result and openai_result['confidence'] > result['confidence']:
                        result = openai_result
                
                ambiguity_result = self._check_ambiguity(result)
                result.update(ambiguity_result)
                
                if result['confidence'] >= self.config.confidence_threshold:
                    return result
                else:
                    logger.debug(
                        f"AI confidence {result['confidence']:.2f} below threshold "
                        f"{self.config.confidence_threshold}, using fallback"
                    )
                    fallback_result = self._classify_with_fallback(text)
                    fallback_result['all_scores'] = result['all_scores']
                    fallback_result['needs_clarification'] = True
                    return fallback_result
                    
            except Exception as e:
                logger.error(f"AI classification failed: {e}")
                # Try OpenAI only
        
        # Try OpenAI only
        if self.use_openai and self.openai_client is not None:
            try:
                result = self._classify_with_openai(text)
                if result:
                    ambiguity_result = self._check_ambiguity(result)
                    result.update(ambiguity_result)
                    
                    if result['confidence'] >= self.config.confidence_threshold:
                        return result
            except Exception as e:
                logger.error(f"OpenAI classification failed: {e}")
        
        # Fallback to keyword-based
        return self._classify_with_fallback(text)
    
    def _classify_with_hybrid(self, text: str) -> Dict[str, Any]:
        """Classify intent using both HuggingFace and OpenAI models in parallel."""
        hf_result = None
        openai_result = None
        
        # Run both classifications in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            hf_future = executor.submit(self._classify_with_ai, text)
            openai_future = executor.submit(self._classify_with_openai, text)
            
            try:
                hf_result = hf_future.result(timeout=self.openai_config.timeout)
            except Exception as e:
                logger.warning(f"HuggingFace classification failed in hybrid: {e}")
            
            try:
                openai_result = openai_future.result(timeout=self.openai_config.timeout)
            except Exception as e:
                logger.warning(f"OpenAI classification failed in hybrid: {e}")
        
        # If only one model succeeded, use that result
        if hf_result is None and openai_result is not None:
            return openai_result
        if openai_result is None and hf_result is not None:
            return hf_result
        if hf_result is None and openai_result is None:
            return self._classify_with_fallback(text)
        
        # Combine results using weighted ensemble
        return self._combine_classifications(hf_result, openai_result)
    
    def _combine_classifications(self, hf_result: Dict[str, Any], openai_result: Dict[str, Any]) -> Dict[str, Any]:
        """Combine classification results from both models using weighted ensemble."""
        # Get intents and scores
        hf_intent = hf_result['intent']
        hf_confidence = hf_result['confidence']
        openai_intent = openai_result['intent']
        openai_confidence = openai_result['confidence']
        
        # Calculate weighted scores
        hf_weighted = hf_confidence * self.hf_weight
        openai_weighted = openai_confidence * self.openai_weight
        
        # Combine all scores
        combined_scores = {}
        
        # Add HuggingFace scores
        for intent, score in hf_result.get('all_scores', {}).items():
            combined_scores[intent] = score * self.hf_weight
        
        # Add OpenAI scores (if available)
        for intent, score in openai_result.get('all_scores', {}).items():
            if intent in combined_scores:
                combined_scores[intent] += score * self.openai_weight
            else:
                combined_scores[intent] = score * self.openai_weight
        
        # Determine final intent
        if hf_intent == openai_intent:
            # Both models agree
            final_intent = hf_intent
            final_confidence = (hf_weighted + openai_weighted) / (self.hf_weight + self.openai_weight)
            model_used = 'hybrid_agreement'
        else:
            # Models disagree - use the one with higher weighted confidence
            if openai_weighted > hf_weighted:
                final_intent = openai_intent
                final_confidence = openai_confidence
                model_used = 'openai_preferred'
            else:
                final_intent = hf_intent
                final_confidence = hf_confidence
                model_used = 'huggingface_preferred'
        
        logger.debug(
            f"Hybrid classification: HF={hf_intent}({hf_confidence:.2f}), "
            f"OpenAI={openai_intent}({openai_confidence:.2f}), "
            f"Final={final_intent}({final_confidence:.2f}), Model={model_used}"
        )
        
        return {
            'intent': final_intent,
            'confidence': float(final_confidence),
            'all_scores': combined_scores,
            'used_fallback': False,
            'is_ambiguous': False,
            'ambiguous_intents': [],
            'needs_clarification': False,
            'model_used': model_used,
            'hf_result': {'intent': hf_intent, 'confidence': hf_confidence},
            'openai_result': {'intent': openai_intent, 'confidence': openai_confidence}
        }
    
    def _classify_with_openai(self, text: str) -> Optional[Dict[str, Any]]:
        """Classify intent using OpenAI-compatible model."""
        if not self.use_openai or self.openai_client is None:
            return None
        
        try:
            # Build the classification prompt
            intent_list = list(self.INTENT_MAPPING.values())
            intent_descriptions = {
                'greeting': 'User is greeting or saying hello',
                'order_status': 'User wants to check order status or tracking',
                'order_history': 'User wants to see their past orders',
                'return_policy': 'User asking about return or refund policy',
                'product_recommendation': 'User wants product recommendations or suggestions',
                'product_search': 'User searching for specific products',
                'product_info': 'User wants information about a specific product',
                'shipping_info': 'User asking about shipping or delivery',
                'warranty_info': 'User asking about warranty',
                'payment_info': 'User asking about payment methods',
                'cancel_order': 'User wants to cancel an order',
                'user_profile': 'User wants to see their profile or account info',
                'general_inquiry': 'General question or help request'
            }
            
            classification_prompt = f"""Classify the following customer message into one of these intents:

{json.dumps(intent_descriptions, indent=2)}

Customer message: "{text}"

Respond with ONLY a JSON object in this exact format:
{{"intent": "intent_name", "confidence": 0.95}}

The confidence should be between 0 and 1."""

            response = self.openai_client.chat.completions.create(
                model=self.openai_config.model_name,
                messages=[
                    {"role": "assistant", "content": self.openai_config.system_prompt},
                    {"role": "user", "content": classification_prompt}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from response
            try:
                # Handle potential markdown code blocks
                if '```' in response_text:
                    response_text = response_text.split('```')[1]
                    if response_text.startswith('json'):
                        response_text = response_text[4:]
                
                result = json.loads(response_text)
                intent = result.get('intent', 'general_inquiry')
                confidence = float(result.get('confidence', 0.5))
                
                # Validate intent
                if intent not in intent_list:
                    intent = 'general_inquiry'
                    confidence = 0.3
                
                return {
                    'intent': intent,
                    'confidence': confidence,
                    'all_scores': {intent: confidence},
                    'used_fallback': False,
                    'is_ambiguous': False,
                    'ambiguous_intents': [],
                    'needs_clarification': False,
                    'model_used': 'openai'
                }
                
            except json.JSONDecodeError:
                # Try to extract intent from plain text response
                response_lower = response_text.lower()
                for intent in intent_list:
                    if intent in response_lower:
                        return {
                            'intent': intent,
                            'confidence': 0.6,
                            'all_scores': {intent: 0.6},
                            'used_fallback': False,
                            'is_ambiguous': False,
                            'ambiguous_intents': [],
                            'needs_clarification': False,
                            'model_used': 'openai'
                        }
                
                logger.warning(f"Could not parse OpenAI response: {response_text}")
                return None
                
        except Exception as e:
            logger.error(f"OpenAI classification error: {e}")
            return None
    
    def _classify_with_ai(self, text: str) -> Dict[str, Any]:
        
        result = self.classifier(
            text,
            candidate_labels=self.config.intent_labels,
            multi_label=False
        )
        
        
        all_scores = {}
        for label, score in zip(result['labels'], result['scores']):
            mapped_intent = self._map_intent(label)
            all_scores[mapped_intent] = score
        
        
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
            'needs_clarification': False,
            'model_used': 'huggingface'
        }
    
    def _check_ambiguity(self, classification_result: Dict[str, Any]) -> Dict[str, Any]:
        
        all_scores = classification_result.get('all_scores', {})
        
        if len(all_scores) < 2:
            return {
                'is_ambiguous': False,
                'ambiguous_intents': [],
                'needs_clarification': False
            }
        
        
        sorted_intents = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
        
        top_intent, top_score = sorted_intents[0]
        second_intent, second_score = sorted_intents[1]
        
        
        score_difference = top_score - second_score
        
        if score_difference < self.config.ambiguity_threshold:
            
            ambiguous_intents = [
                {'intent': top_intent, 'score': top_score},
                {'intent': second_intent, 'score': second_score}
            ]
            
            
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
            'confidence': 0.5,  
            'all_scores': {intent: 0.5},
            'used_fallback': True,
            'is_ambiguous': False,
            'ambiguous_intents': [],
            'needs_clarification': False,
            'model_used': 'keyword_fallback'
        }

    
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
        
        
        order_id = self._extract_order_id(text)
        if order_id:
            entities['order_id'] = order_id
            entities['has_order_id'] = True
        
        
        product_id = self._extract_product_id(text)
        if product_id:
            entities['product_id'] = product_id
            entities['has_product_id'] = True
        
        
        max_price, min_price = self._extract_prices(text)
        if max_price is not None:
            entities['max_price'] = max_price
        if min_price is not None:
            entities['min_price'] = min_price
        
        
        category = self._extract_category(text)
        if category:
            entities['category'] = category
        
        
        features = self._extract_features(text)
        if features:
            entities['features'] = features
        
        
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
        
        pattern = r'P\d{3}'
        match = re.search(pattern, text.upper())
        return match.group(0) if match else None
    
    def _extract_prices(self, text: str) -> tuple:
        
        text_lower = text.lower()
        max_price = None
        min_price = None
        
        
        under_patterns = [
            r'(?:under|below|less than|cheaper than|max|maximum)\s*\$(\d+(?:\.\d{2})?)',
            r'(?:under|below|less than|cheaper than|max|maximum)\s*(\d+(?:\.\d{2})?)\s*dollars?'
        ]
        
        for pattern in under_patterns:
            match = re.search(pattern, text_lower)
            if match:
                max_price = float(match.group(1))
                break
        
        
        over_patterns = [
            r'(?:over|above|more than|at least|min|minimum)\s*\$(\d+(?:\.\d{2})?)',
            r'(?:over|above|more than|at least|min|minimum)\s*(\d+(?:\.\d{2})?)\s*dollars?'
        ]
        
        for pattern in over_patterns:
            match = re.search(pattern, text_lower)
            if match:
                min_price = float(match.group(1))
                break
        
        
        if max_price is None and min_price is None:
            
            dollar_pattern = r'\$(\d+(?:\.\d{2})?)'
            match = re.search(dollar_pattern, text)
            if match:
                max_price = float(match.group(1))
            else:
                
                dollars_pattern = r'(\d+(?:\.\d{2})?)\s*dollars?'
                match = re.search(dollars_pattern, text_lower)
                if match:
                    max_price = float(match.group(1))
        
        return max_price, min_price
    
    def _extract_category(self, text: str) -> Optional[str]:
        
        text_lower = text.lower()
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_lower):
                    return category
        
        return None
    
    def _extract_features(self, text: str) -> List[str]:
        
        text_lower = text.lower()
        found_features = []
        
        for feature in self.FEATURE_KEYWORDS:
            
            pattern = r'\b' + re.escape(feature) + r'\b'
            if re.search(pattern, text_lower):
                
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
        
        
        
        patterns = [
            r'\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z]?[a-zA-Z0-9]+)*)\s+(?:case|cover|charger|cable|accessory|accessories)',
            r'(?:looking for|find|search for|want|need)\s+(?:a\s+)?([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*)',
            r'(?:do you have|have any)\s+([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                product_name = match.group(1).strip()
                
                non_products = ['the', 'a', 'an', 'some', 'any', 'good', 'best', 'cheap', 'expensive']
                if product_name.lower() not in non_products and len(product_name) > 1:
                    return product_name
        
        return None
    
    def _preprocess_text(self, text: str) -> str:
        
        
        text = ' '.join(text.split())
        
        
        
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
        
        
        processed_text = self._preprocess_text(text)
        
        
        classification = self.classify_intent(processed_text)
        
        
        entities = self.extract_entities(text)  
        
        
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
        
        
        for key in ['order_id', 'product_id', 'category', 'product_name']:
            if entities.get(key) is None and context_entities.get(key) is not None:
                entities[key] = context_entities[key]
                
                if key == 'order_id':
                    entities['has_order_id'] = True
                elif key == 'product_id':
                    entities['has_product_id'] = True
        
        return entities

    
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
    
    def generate_enhanced_response(self, user_message: str, base_response: str, intent: str) -> str:
        """
        Use OpenAI model to enhance or improve a response.
        
        Args:
            user_message: Original user message
            base_response: The base response from the system
            intent: Detected intent
            
        Returns:
            Enhanced response string
        """
        if not self.use_openai or self.openai_client is None:
            return base_response
        
        try:
            enhancement_prompt = f"""You are an e-commerce customer support assistant. 
A customer asked: "{user_message}"

The system generated this response:
{base_response}

Please improve this response to be more helpful, friendly, and complete while keeping the same information. 
Keep the emoji formatting if present. Be concise but thorough.
If the response is already good, return it as-is with minor improvements.

Return ONLY the improved response text, nothing else."""

            response = self.openai_client.chat.completions.create(
                model=self.openai_config.model_name,
                messages=[
                    {"role": "assistant", "content": self.openai_config.system_prompt},
                    {"role": "user", "content": enhancement_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            enhanced = response.choices[0].message.content.strip()
            
            # Validate the response isn't empty or too different
            if enhanced and len(enhanced) > 10:
                return enhanced
            
            return base_response
            
        except Exception as e:
            logger.warning(f"Response enhancement failed: {e}")
            return base_response
    
    def generate_conversational_response(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Generate a conversational response using OpenAI for general queries.
        
        Args:
            user_message: User's message
            context: Optional conversation context
            
        Returns:
            Generated response or None if failed
        """
        if not self.use_openai or self.openai_client is None:
            return None
        
        try:
            # Build context-aware prompt
            context_info = ""
            if context:
                if context.get('user_id'):
                    context_info += "The user is logged in. "
                if context.get('order_id'):
                    context_info += f"They mentioned order {context.get('order_id')}. "
                if context.get('product_id'):
                    context_info += f"They're asking about product {context.get('product_id')}. "
            
            prompt = f"""You are a helpful e-commerce customer support assistant.
{context_info}

Customer message: "{user_message}"

Provide a helpful, friendly response. If you need more information to help them, ask clarifying questions.
Keep responses concise and use emojis where appropriate (📦 for orders, 🛍️ for products, etc.).

Important: Only answer questions related to e-commerce (orders, products, shipping, returns, payments, account).
For unrelated questions, politely redirect them to e-commerce topics."""

            response = self.openai_client.chat.completions.create(
                model=self.openai_config.model_name,
                messages=[
                    {"role": "assistant", "content": self.openai_config.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Conversational response generation failed: {e}")
            return None
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get the status of all AI models."""
        return {
            'huggingface': {
                'enabled': self.use_ai,
                'model': self.config.model_name if self.use_ai else None,
                'weight': self.hf_weight
            },
            'openai': {
                'enabled': self.use_openai,
                'model': self.openai_config.model_name if self.use_openai else None,
                'weight': self.openai_weight,
                'api_url': self.openai_config.api_base_url if self.use_openai else None
            },
            'hybrid_mode': self.use_ai and self.use_openai,
            'fallback_available': True  # Keyword-based fallback is always available
        }
