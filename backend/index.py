import os
import sys

# Add the current directory to sys.path so that imports from 'services', 'routes', etc. work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app

# Vercel needs the 'app' object to be available at the module level
# This file serves as the entry point for Vercel Serverless Functions
