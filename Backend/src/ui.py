"""
User Interface Module
Implements command-line interface for chatbot interaction
"""

import sys

class ChatbotUI:
    """Simple command-line interface for the chatbot"""
    
    def __init__(self, agent):
        self.agent = agent
    
    def display_welcome(self):
        """Display welcome message"""
        print("\n" + "="*70)
        print("  🛍️  E-SHOP CUSTOMER SUPPORT CHATBOT")
        print("="*70)
        print("\n🤖 Hello! I'm your AI customer support assistant.")
        print("\n📋 I can help you with:")
        print("  • 📦 Order status and tracking")
        print("  • 🔄 Return policy and procedures")
        print("  • 🛍️  Product recommendations")
        print("  • 🚚 Shipping information")
        print("  • 💳 Payment methods")
        print("  • 🛡️  Warranty information")
        print("\n💡 Tips:")
        print("  - Mention order numbers like: ORD12345")
        print("  - Ask about specific products: P001")
        print("  - Type 'help' for assistance")
        print("  - Type 'exit' to quit")
        print("\n" + "="*70 + "\n")
    
    def display_thinking(self):
        """Display thinking indicator"""
        print("🤖 Chatbot: ", end="", flush=True)
        print("Thinking...", end="\r", flush=True)
    
    def clear_thinking(self):
        """Clear thinking indicator"""
        print(" " * 50, end="\r", flush=True)
    
    def display_response(self, response):
        """Display chatbot response"""
        print(f"🤖 Chatbot:\n{response}\n")
    
    def get_user_input(self):
        """Get input from user"""
        try:
            user_input = input("👤 You: ").strip()
            return user_input
        except EOFError:
            return "exit"
        except KeyboardInterrupt:
            return "exit"
    
    def display_goodbye(self):
        """Display goodbye message"""
        print("\n" + "="*70)
        print("🤖 Thank you for contacting E-Shop Customer Support!")
        print("   Have a great day! 👋")
        print("="*70 + "\n")
    
    def display_error(self, error):
        """Display error message"""
        print(f"\n❌ Error: {error}\n")
    
    def run(self):
        """Main UI loop"""
        self.display_welcome()
        
        while True:
            try:
                # Get user input
                user_input = self.get_user_input()
                
                # Check for empty input
                if not user_input:
                    continue
                
                # Check for exit commands
                if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye', 'q']:
                    self.display_goodbye()
                    break
                
                # Show thinking indicator
                self.display_thinking()
                
                # Get response from agent
                response = self.agent.run(user_input)
                
                # Clear thinking indicator and display response
                self.clear_thinking()
                self.display_response(response)
                
            except KeyboardInterrupt:
                print("\n")
                self.display_goodbye()
                break
            except Exception as e:
                self.clear_thinking()
                self.display_error(str(e))
                print("Let's try again...\n")
