"""
Main Entry Point for E-commerce Customer Support Chatbot
Demonstrates: Complete AI system integrating all components
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.dirname(__file__))

from src.agent import CustomerSupportAgent
from src.ui import ChatbotUI

def main():
    """Main entry point for the chatbot"""
    try:
        print("\n🚀 Starting E-Shop Customer Support Chatbot...")
        print("📚 Loading knowledge base...")
        
        # Initialize agent with data directory
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        agent = CustomerSupportAgent(data_dir)
        
        print("✅ Knowledge base loaded successfully!")
        print("✅ Inference engine initialized!")
        print("✅ Agent ready!\n")
        
        # Initialize UI
        ui = ChatbotUI(agent)
        
        # Run chatbot
        ui.run()
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: Required data file not found - {e}")
        print("Please ensure all data files are in the 'data' directory.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check your installation and try again.")

if __name__ == "__main__":
    main()
