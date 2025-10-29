import os
import sys


TEST_DIR = os.path.dirname(__file__)
SERVICE_ROOT = os.path.abspath(os.path.join(TEST_DIR, ".."))

if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)


