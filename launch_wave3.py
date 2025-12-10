import subprocess
import sys
import time
import os

# The categories defined in import_wave3_expansion.py
CATEGORIES = [
    "Vacuums", 
    "Sports", 
    "Household"
]

def launch_wave3_parallel():
    print(f"🚀 Launching Wave 3 Expansion ({len(CATEGORIES)} workers)...")
    print("=" * 60)
    
    processes = []
    
    venv_python = os.path.join(os.getcwd(), "venv", "bin", "python3")
    if os.path.exists(venv_python):
        python_exe = venv_python
    else:
        python_exe = sys.executable
        
    print(f"Using Python: {python_exe}")

    for category in CATEGORIES:
        print(f"   Starting worker for: {category}")
        
        log_file = open(f"logs/wave3_{category.replace(' ', '_').lower()}.log", "w")
        
        p = subprocess.Popen(
            [python_exe, "import_wave3_expansion.py", "--category", category],
            stdout=log_file,
            stderr=log_file
        )
        
        processes.append({
            "category": category,
            "process": p,
            "log_file": log_file
        })
        
        time.sleep(2)

    print("=" * 60)
    print(f"✅ All Wave 3 workers started!")
    print("   Logs are being written to the 'logs/' directory (prefix: wave3_).")
    print("=" * 60)
    
    try:
        while True:
            active = 0
            for p_info in processes:
                if p_info["process"].poll() is None:
                    active += 1
            
            if active == 0:
                print("\n✨ All Wave 3 workers have completed!")
                break
                
            print(f"\r   🔄 Active Wave 3 Workers: {active}/{len(processes)}", end="")
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping Wave 3 workers...")
        for p_info in processes:
            p_info["process"].terminate()
        print("   All processes terminated.")

if __name__ == "__main__":
    if not os.path.exists("logs"):
        os.makedirs("logs")
        
    launch_wave3_parallel()
