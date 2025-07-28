#!/usr/bin/env python3
"""
Backend runner script for Debabelize Me application.
Handles environment setup and starts the uvicorn server.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def check_requirements():
    """Check if required dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        import openai
        import pydantic_settings
        print("✓ All dependencies installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e.name}")
        print("\nPlease install requirements:")
        print("  pip install -r requirements.txt")
        return False

def check_env():
    """Check if .env file exists and has required variables."""
    env_file = backend_dir / ".env"
    if not env_file.exists():
        print("✗ .env file not found")
        print("\nPlease create .env file with:")
        print("  OPENAI_API_KEY=your-api-key-here")
        return False
    
    # Check for OPENAI_API_KEY
    with open(env_file) as f:
        env_content = f.read()
        if "OPENAI_API_KEY" not in env_content:
            print("✗ OPENAI_API_KEY not found in .env")
            return False
    
    print("✓ Environment configured")
    return True

def main():
    """Main runner function."""
    print("Debabelize Me Backend Runner")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment
    if not check_env():
        sys.exit(1)
    
    # Run the server
    print("\nStarting FastAPI server...")
    print(f"Server will run on: http://localhost:8005")
    print("API docs available at: http://localhost:8005/docs")
    print("\nPress CTRL+C to stop\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--reload",
            "--port", "8005",
            "--host", "0.0.0.0"
        ])
    except KeyboardInterrupt:
        print("\n\nServer stopped.")

if __name__ == "__main__":
    main()