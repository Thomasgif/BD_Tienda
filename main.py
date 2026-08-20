import os
import sys

# Asegurar que la carpeta 'src' este en sys.path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from gui.login import LoginWindow

def main():
    app = LoginWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
