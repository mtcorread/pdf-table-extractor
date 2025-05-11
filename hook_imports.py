import os
import sys

# Add your project's root directory to the path
module_dir = os.path.dirname(sys.modules['__main__'].__file__)
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)