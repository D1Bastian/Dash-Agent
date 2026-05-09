import sys
import os

# Add the root directory to the path so we can import backend and superpowers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

# Vercel needs the app object
handler = app
