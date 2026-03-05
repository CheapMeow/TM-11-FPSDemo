"""
Main entry point for the PBR rendering application
"""
import sys
import ctypes
from app.app import PBRApp


def main():
    app = PBRApp()
    if not app.init():
        print("Failed to initialize application")
        sys.exit(1)
    app.run()
    app.cleanup()


if __name__ == "__main__":
    main()
