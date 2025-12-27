
import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class NLPConfig:
    """
    Configuration for the AI NLP Processor.
    
    Attributes:
        model_name: Hugging Face model for zero-shot classification
        confidence_threshold: Minimum confidence to use AI classification (fallback below this)
        ambiguity_threshold: Difference threshold for requesting clarification
        intent_labels: List of intent labels for zero-shot classification
    """
    model_name: str = "facebook/bart-large-mnli"
    confidence_threshold: float = 0.4
    ambiguity_threshold: float = 0.1
    intent_labels: List[str] = field(default_factory=lambda: [
        "greeting",
        "order status inquiry",
        "order history request",
        "return policy question",
        "product recommendation request",
        "product search",
        "product information request",
        "shipping information",
        "warranty information",
        "payment information",
        "order cancellation",
        "user profile request",
        "general help"
    ])
    
    @classmethod
    def from_env(cls) -> "NLPConfig":
        """
        Create NLPConfig from environment variables.
        
        Environment Variables:
            NLP_MODEL_NAME: Hugging Face model name (default: facebook/bart-large-mnli)
            NLP_CONFIDENCE_THRESHOLD: Fallback threshold (default: 0.4)
            NLP_AMBIGUITY_THRESHOLD: Clarification threshold (default: 0.1)
            NLP_INTENT_LABELS: Comma-separated intent labels (optional)
        
        Returns:
            NLPConfig instance with values from environment or defaults
        """
        config = cls()
        
        # Load model name from environment
        model_name = os.getenv("NLP_MODEL_NAME")
        if model_name:
            config.model_name = model_name
        
        # Load confidence threshold from environment
        confidence_threshold = os.getenv("NLP_CONFIDENCE_THRESHOLD")
        if confidence_threshold:
            try:
                config.confidence_threshold = float(confidence_threshold)
            except ValueError:
                pass  # Keep default if invalid
        
        # Load ambiguity threshold from environment
        ambiguity_threshold = os.getenv("NLP_AMBIGUITY_THRESHOLD")
        if ambiguity_threshold:
            try:
                config.ambiguity_threshold = float(ambiguity_threshold)
            except ValueError:
                pass  # Keep default if invalid
        
        # Load intent labels from environment (comma-separated)
        intent_labels = os.getenv("NLP_INTENT_LABELS")
        if intent_labels:
            labels = [label.strip() for label in intent_labels.split(",") if label.strip()]
            if labels:
                config.intent_labels = labels
        
        return config


@dataclass
class OpenAIConfig:
    """
    Configuration for the OpenAI-compatible model (AIML API).
    
    Attributes:
        api_base_url: Base URL for the OpenAI-compatible API
        api_key: API key for authentication
        model_name: Model name to use (e.g., openai/gpt-oss-20b)
        enabled: Whether to use the OpenAI model
        timeout: Request timeout in seconds
        weight: Weight for ensemble scoring (0-1)
        system_prompt: System prompt for the assistant role
    """
    api_base_url: str = "https://api.aimlapi.com/v1"
    api_key: Optional[str] = None
    model_name: str = "openai/gpt-oss-20b"
    enabled: bool = True
    timeout: int = 30
    weight: float = 0.6
    system_prompt: str = "You are an e-commerce platform assistant. Help customers with orders, products, returns, shipping, and general inquiries. Be helpful, concise, and friendly."
    
    @classmethod
    def from_env(cls) -> "OpenAIConfig":
        """
        Create OpenAIConfig from environment variables.
        
        Environment Variables:
            OPENAI_API_BASE_URL: API base URL (default: https://api.aimlapi.com/v1)
            OPENAI_API_KEY: API key for authentication
            OPENAI_MODEL_NAME: Model name (default: openai/gpt-oss-20b)
            OPENAI_ENABLED: Enable/disable OpenAI model (default: true)
            OPENAI_TIMEOUT: Request timeout in seconds (default: 30)
            OPENAI_WEIGHT: Weight for ensemble scoring (default: 0.6)
        
        Returns:
            OpenAIConfig instance with values from environment or defaults
        """
        config = cls()
        
        # Load API base URL
        api_base_url = os.getenv("OPENAI_API_BASE_URL")
        if api_base_url:
            config.api_base_url = api_base_url
        
        # Load API key
        config.api_key = os.getenv("OPENAI_API_KEY")
        
        # Load model name
        model_name = os.getenv("OPENAI_MODEL_NAME")
        if model_name:
            config.model_name = model_name
        
        # Load enabled flag
        enabled = os.getenv("OPENAI_ENABLED", "true").lower()
        config.enabled = enabled in ("true", "1", "yes")
        
        # Load timeout
        timeout = os.getenv("OPENAI_TIMEOUT")
        if timeout:
            try:
                config.timeout = int(timeout)
            except ValueError:
                pass
        
        # Load weight
        weight = os.getenv("OPENAI_WEIGHT")
        if weight:
            try:
                config.weight = float(weight)
            except ValueError:
                pass
        
        return config
    
    def is_configured(self) -> bool:
        """Check if the OpenAI config has required settings."""
        return self.enabled and self.api_key is not None and len(self.api_key) > 0


# Default configuration instances
default_config = NLPConfig()
default_openai_config = OpenAIConfig()
