import subprocess
import time
import sys
import os

# Wave 4 Categories
CATEGORIES = ["Beauty", "Pets", "Tools", "Baby", "Clothing"]

processes = []

print(f"🚀 Launching Wave 4 Parallel Import Workers ({len(CATEGORIES)} processes)...")

# Determine Python executable
venv_python = os.path.join(os.getcwd(), "venv", "bin", "python3")
if os.path.exists(venv_python):
    python_executable = venv_python
else:
    python_executable = sys.executable

print(f"Using Python: {python_executable}")

for category in CATEGORIES:
    print(f"   ▶️ Starting worker for: {category}")
    
    # Launch a separate Python process for each category
    p = subprocess.Popen([
        python_executable, 
        "import_wave4_expansion.py", 
        "--category", 
        category
    ])
    processes.append(p)
    
    # Stagger starts to avoid initial API spike
    time.sleep(5)

print("\n✅ All Wave 4 workers launched! Monitoring...")

try:
    # Wait for all processes to complete
    for p in processes:
        p.wait()
    print("\n✨ All Wave 4 imports completed successfully.")
except KeyboardInterrupt:
    print("\n🛑 Stopping all workers...")
    for p in processes:
        p.terminate()
