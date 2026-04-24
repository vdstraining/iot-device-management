import sys
import os

# Ensure the project root is on sys.path so that ui, ws_client,
# utilities, http_client are importable from any test sub-directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
