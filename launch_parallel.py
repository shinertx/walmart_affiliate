import subprocess
import sys
import time
import os

# The categories defined in import_wave2_bestsellers.py
CATEGORIES = [
    "Electronics", 
    "Home", 
    "Toys", 
    "Sports", 
    "Automotive", 
    "Office", 
    "Patio & Garden"
]

def launch_parallel_imports():
    print(f"🚀 Launching {len(CATEGORIES)} parallel import workers...")
    print("=" * 60)
    
    processes = []
    
    # Determine python executable
    # Prefer the venv python if it exists, otherwise system python
    venv_python = os.path.join(os.getcwd(), "venv", "bin", "python3")
    if os.path.exists(venv_python):
        python_exe = venv_python
    else:
        python_exe = sys.executable
        
    print(f"Using Python: {python_exe}")

    for category in CATEGORIES:
        print(f"   Starting worker for: {category}")
        
        # Create a log file for each worker
        log_file = open(f"logs/import_{category.replace(' ', '_').lower()}.log", "w")
        
        # Launch the process
        p = subprocess.Popen(
            [python_exe, "import_wave2_bestsellers.py", "--category", category],
            stdout=log_file,
            stderr=log_file
        )
        
        processes.append({
            "category": category,
            "process": p,
            "log_file": log_file
        })
        
        # Stagger starts slightly to avoid API rate limit spikes on startup
        time.sleep(2)

    print("=" * 60)
    print(f"✅ All {len(processes)} workers started!")
    print("   Logs are being written to the 'logs/' directory.")
    print("   Monitor progress with: tail -f logs/*.log")
    print("=" * 60)
    
    try:
        # Monitor loop
        while True:
            active = 0
            for p_info in processes:
                if p_info["process"].poll() is None:
                    active += 1
            
            if active == 0:
                print("\n✨ All workers have completed!")
                break
                
            print(f"\r   🔄 Active Workers: {active}/{len(processes)}", end="")
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping all workers...")
        for p_info in processes:
            p_info["process"].terminate()
        print("   All processes terminated.")

if __name__ == "__main__":
    # Ensure logs directory exists
    if not os.path.exists("logs"):
        os.makedirs("logs")
        
    launch_parallel_imports()
