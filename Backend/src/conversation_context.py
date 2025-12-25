"""
Conversation Context Management for E-Shop Chatbot.

This module provides conversation context tracking for follow-up questions
and multi-turn conversations. It maintains entity references and detects
topic changes.

Requirements: 4.1, 4.2, 4.3
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ConversationExchange:
    """
    Represents a single exchange in the conversation.
    
    Attributes:
        user_input: The user's message
        intent: Classified intent for the message
        entities: Extracted entities from the message
        response: System response to the message
        timestamp: When the exchange occurred
    """
    user_input: str
    intent: str
    entities: Dict[str, Any]
    response: str
    timestamp: datetime = field(default_factory=datetime.now)


class ConversationContext:
    """
    Manages conversation context for follow-up questions.
    
    Maintains a history of conversation exchanges and provides context
    for understanding follow-up questions. Limits history to a configurable
    maximum number of exchanges.
    
    Attributes:
        max_history: Maximum number of exchanges to retain (default: 5)
        history: List of ConversationExchange objects
        auth_state: Preserved authentication state
    
    Requirements: 4.1, 4.2, 4.3
    """
    
    # Intent groups for topic change detection
    INTENT_GROUPS = {
        'order': ['order_status', 'order_history', 'cancel_order'],
        'product': ['product_search', 'product_recommendation', 'product_info'],
        'policy': ['return_policy', 'shipping_info', 'warranty_info', 'payment_info'],
        'account': ['user_profile', 'greeting'],
        'general': ['general_inquiry', 'general_help']
    }
    
    def __init__(self, max_history: int = 5):
        """
        Initialize conversation context with maximum history length.
        
        Args:
            max_history: Maximum number of exchanges to retain (default: 5)
        
        Requirements: 4.2
        """
        self.max_history = max_history
        self.history: List[ConversationExchange] = []
        self.auth_state: Optional[Dict[str, Any]] = None
    
    def add_exchange(
        self,
        user_input: str,
        intent: str,
        entities: Dict[str, Any],
        response: str
    ) -> None:
        """
        Add a conversation exchange to history.
        
        Adds the exchange and trims history if it exceeds max_history.
        
        Args:
            user_input: The user's message
            intent: Classified intent for the message
            entities: Extracted entities from the message
            response: System response to the message
        
        Requirements: 4.1, 4.2
        """
        exchange = ConversationExchange(
            user_input=user_input,
            intent=intent,
            entities=entities,
            response=response
        )
        
        self.history.append(exchange)
        
        # Trim history to max_history limit
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_context(self) -> Dict[str, Any]:
        """
        Get current context including recent entities.
        
        Aggregates entities from recent exchanges, with more recent
        exchanges taking precedence for conflicting values.
        
        Returns:
            Dictionary containing:
                - entities: Aggregated entities from recent exchanges
                - last_intent: Most recent intent
                - exchange_count: Number of exchanges in history
                - auth_state: Current authentication state
        
        Requirements: 4.1
        """
        if not self.history:
            return {
                'entities': {},
                'last_intent': None,
                'exchange_count': 0,
                'auth_state': self.auth_state
            }
        
        # Aggregate entities from history (older first, newer overwrites)
        aggregated_entities: Dict[str, Any] = {}
        
        for exchange in self.history:
            for key, value in exchange.entities.items():
                # Only update if value is not None/empty
                if value is not None and value != [] and value != '':
                    aggregated_entities[key] = value
        
        return {
            'entities': aggregated_entities,
            'last_intent': self.history[-1].intent if self.history else None,
            'exchange_count': len(self.history),
            'auth_state': self.auth_state
        }
    
    def clear(self) -> None:
        """
        Clear conversation context.
        
        Removes all history but preserves authentication state.
        
        Requirements: 4.3
        """
        self.history = []
        # Note: auth_state is preserved as per requirement 4.3
    
    def clear_all(self) -> None:
        """
        Clear all context including authentication state.
        
        Use this for complete session reset.
        """
        self.history = []
        self.auth_state = None
    
    def set_auth_state(self, auth_state: Optional[Dict[str, Any]]) -> None:
        """
        Set the authentication state.
        
        Args:
            auth_state: Authentication state dictionary with user_id, role, etc.
        """
        self.auth_state = auth_state
    
    def get_auth_state(self) -> Optional[Dict[str, Any]]:
        """
        Get the current authentication state.
        
        Returns:
            Authentication state dictionary or None if not authenticated
        """
        return self.auth_state
    
    def _get_intent_group(self, intent: str) -> str:
        """
        Get the topic group for an intent.
        
        Args:
            intent: Intent name
            
        Returns:
            Topic group name
        """
        for group, intents in self.INTENT_GROUPS.items():
            if intent in intents:
                return group
        return 'general'
    
    def detect_topic_change(self, new_intent: str) -> bool:
        """
        Detect if user changed topic.
        
        Compares the new intent's topic group with the previous intent's
        topic group to determine if a topic change occurred.
        
        Args:
            new_intent: The newly classified intent
            
        Returns:
            True if topic changed, False otherwise
        
        Requirements: 4.3
        """
        if not self.history:
            return False
        
        last_intent = self.history[-1].intent
        
        # Get topic groups
        last_group = self._get_intent_group(last_intent)
        new_group = self._get_intent_group(new_intent)
        
        # Topic change if groups differ (excluding general which is neutral)
        if last_group == 'general' or new_group == 'general':
            return False
        
        return last_group != new_group
    
    def handle_topic_change(self, new_intent: str) -> bool:
        """
        Handle topic change by clearing irrelevant context.
        
        If a topic change is detected, clears the conversation history
        but preserves authentication state.
        
        Args:
            new_intent: The newly classified intent
            
        Returns:
            True if topic changed and context was cleared, False otherwise
        
        Requirements: 4.3
        """
        if self.detect_topic_change(new_intent):
            self.clear()  # Clears history but preserves auth_state
            return True
        return False
    
    def get_recent_entities(self, entity_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get specific entities from recent context.
        
        Args:
            entity_keys: List of entity keys to retrieve. If None, returns all.
            
        Returns:
            Dictionary of requested entities
        """
        context = self.get_context()
        all_entities = context.get('entities', {})
        
        if entity_keys is None:
            return all_entities
        
        return {key: all_entities.get(key) for key in entity_keys if key in all_entities}
    
    def has_entity(self, entity_key: str) -> bool:
        """
        Check if a specific entity exists in context.
        
        Args:
            entity_key: The entity key to check
            
        Returns:
            True if entity exists and has a value, False otherwise
        """
        context = self.get_context()
        entities = context.get('entities', {})
        value = entities.get(entity_key)
        return value is not None and value != [] and value != ''
    
    def get_history_summary(self) -> List[Dict[str, Any]]:
        """
        Get a summary of conversation history.
        
        Returns:
            List of dictionaries with user_input, intent, and timestamp
        """
        return [
            {
                'user_input': exchange.user_input,
                'intent': exchange.intent,
                'timestamp': exchange.timestamp.isoformat()
            }
            for exchange in self.history
        ]
