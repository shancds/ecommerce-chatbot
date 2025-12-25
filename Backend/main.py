import sys
import os
import argparse

# Add src directory to path
sys.path.insert(0, os.path.dirname(__file__))


def run_cli_mode():
    from src.agent import CustomerSupportAgent
    from src.ui import ChatbotUI
    
    print("\nStarting E-Shop Customer Support Chatbot (CLI Mode)...")
    print("Loading knowledge base from JSON files...")
    
    # Initialize agent with data directory
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    agent = CustomerSupportAgent(data_dir)
    
    print("Knowledge base loaded successfully!")
    print("Inference engine initialized!")
    print("Agent ready!\n")
    
    # Initialize UI
    ui = ChatbotUI(agent)
    
    # Run chatbot
    ui.run()


def run_api_mode(host='0.0.0.0', port=5000, debug=False):
    from src.api import app, init_app, shutdown
    
    print("\nStarting E-Shop Customer Support Chatbot (API Mode)...")
    print("Connecting to PostgreSQL database...")
    
    try:
        init_app()
        print(f"Server running at http://{host}:{port}")
        print("Endpoints:")
        print(f"POST http://{host}:{port}/api/chat")
        print(f"GET  http://{host}:{port}/api/health")
        print("\nPress Ctrl+C to stop the server.\n")
        
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        shutdown()
        print("Server stopped gracefully.")
    except Exception as e:
        print(f"\nFailed to start API: {e}")
        shutdown()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='E-Shop Customer Support Chatbot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
  python main.py --mode api --port 8080  # Run API on port 8080
        """
    )
    
    parser.add_argument(
        '--mode', '-m',
        choices=['cli', 'api'],
        default='cli',
        help='Run mode: cli (interactive terminal) or api (REST server)'
    )
    
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host address for API mode (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=5000,
        help='Port number for API mode (default: 5000)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode for API (not recommended for production)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'cli':
            run_cli_mode()
        else:
            run_api_mode(host=args.host, port=args.port, debug=args.debug)
            
    except FileNotFoundError as e:
        print(f"\nError: Required data file not found - {e}")
        print("Please ensure all data files are in the 'data' directory.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("Please check your installation and try again.")
        sys.exit(1)


if __name__ == "__main__":
    run_api_mode()
