#!/usr/bin/env python3
"""
Launcher script for the AI Crypto Trading Bot.
This script provides a simple way to start the application.
"""
import sys
import os
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has required variables."""
    env_path = Path('.env')
    
    if not env_path.exists():
        print("❌ Error: .env file not found!")
        print("\n📝 Please create a .env file with your configuration:")
        print("   1. Copy .env.example to .env")
        print("   2. Add your xAI API key to the XAI_API_KEY variable")
        print("\nExample:")
        print("   cp .env.example .env")
        print("   # Then edit .env and add your API key")
        return False
    
    # Check if XAI_API_KEY is set
    with open(env_path, 'r') as f:
        content = f.read()
        if 'your_xai_api_key_here' in content or 'XAI_API_KEY=' not in content:
            print("⚠️  Warning: XAI_API_KEY may not be configured properly in .env")
            print("   Please make sure to set your actual xAI API key")
            return True  # Continue anyway, let the app handle the error
    
    return True

def main():
    """Main entry point."""
    print("🤖 AI Crypto Trading Bot")
    print("=" * 50)
    
    # Check environment
    if not check_env_file():
        sys.exit(1)
    
    print("\n✅ Configuration check passed")
    print("\n🚀 Starting the application...")
    print("   Backend API: http://localhost:8000")
    print("   Web Interface: http://localhost:8000")
    print("\n📊 Press Ctrl+C to stop the server\n")
    print("=" * 50)
    
    # Import and run the application
    try:
        import uvicorn
        from backend.main import app
        from backend.config import settings
        
        uvicorn.run(
            app,
            host=settings.backend_host,
            port=settings.backend_port,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")
        sys.exit(0)
    except ImportError as e:
        print(f"\n❌ Error: Missing dependency - {e}")
        print("\n📦 Please install required packages:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

