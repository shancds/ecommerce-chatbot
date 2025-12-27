
import os
from dataclasses import dataclass, field
from typing import List


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


# Default configuration instance
default_config = NLPConfig()
