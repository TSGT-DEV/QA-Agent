import sys
from pathlib import Path

# Ensure the project root is in the path for absolute imports (so we can import src.qa_agent.ui)
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

def greet(name: str) -> str:
    return f"Hello, {name}!"

if __name__ == "__main__":
    # Import and launch the UI
    from src.qa_agent.ui import launch_ui
    launch_ui()