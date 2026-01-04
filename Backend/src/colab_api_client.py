"""
Colab API Client Module
Handles communication with the external TinyLlama model hosted on Google Colab via ngrok.
"""

import os
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ColabAPIClient:
    """
    Client for communicating with the Colab-hosted TinyLlama model API.
    
    The Colab API handles platform-related policy questions while the local
    inference engine handles order-specific and data queries.
    """
    
    def __init__(self):
        """Initialize the Colab API client with configuration from environment."""
        self.api_url = os.getenv('COLAB_API_URL', '')
        self.timeout = int(os.getenv('COLAB_API_TIMEOUT', '30'))
        self.enabled = os.getenv('COLAB_API_ENABLED', 'true').lower() == 'true'
        
        if self.enabled and self.api_url:
            logger.info(f"Colab API client initialized: {self.api_url}")
        elif self.enabled and not self.api_url:
            logger.warning("Colab API enabled but COLAB_API_URL not set")
            self.enabled = False
    
    def is_available(self) -> bool:
        """Check if the Colab API is configured and enabled."""
        return self.enabled and bool(self.api_url)
    
    def ask(self, question: str) -> Optional[str]:
        """
        Send a question to the Colab API and get a response.
        
        Args:
            question: The user's question about platform policies
            
        Returns:
            The AI-generated answer or None if the request fails
        """
        if not self.is_available():
            logger.debug("Colab API not available, skipping")
            return None
        
        try:
            # Ensure URL ends properly
            endpoint = self.api_url.rstrip('/') + '/ask'
            
            payload = {"question": question}
            
            logger.info(f"Sending request to Colab API: {endpoint}")
            
            response = requests.post(
                endpoint,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', '')
                
                if answer:
                    logger.info("Received successful response from Colab API")
                    return answer
                else:
                    logger.warning("Colab API returned empty answer")
                    return None
            else:
                logger.error(f"Colab API returned status {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Colab API request timed out after {self.timeout}s")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Failed to connect to Colab API: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Colab API request failed: {e}")
            return None
        except ValueError as e:
            logger.error(f"Failed to parse Colab API response: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling Colab API: {e}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Colab API.
        
        Returns:
            Dict with status information
        """
        if not self.is_available():
            return {
                'status': 'disabled',
                'url': self.api_url or 'not configured',
                'message': 'Colab API is not enabled or configured'
            }
        
        try:
            endpoint = self.api_url.rstrip('/') + '/health'
            response = requests.get(endpoint, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'healthy',
                    'url': self.api_url,
                    'model': data.get('model', 'unknown'),
                    'message': 'Colab API is responding'
                }
            else:
                return {
                    'status': 'unhealthy',
                    'url': self.api_url,
                    'message': f'API returned status {response.status_code}'
                }
                
        except requests.exceptions.Timeout:
            return {
                'status': 'timeout',
                'url': self.api_url,
                'message': 'Health check timed out'
            }
        except requests.exceptions.ConnectionError:
            return {
                'status': 'unreachable',
                'url': self.api_url,
                'message': 'Cannot connect to Colab API'
            }
        except Exception as e:
            return {
                'status': 'error',
                'url': self.api_url,
                'message': str(e)
            }
