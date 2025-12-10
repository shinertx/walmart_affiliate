import os
import re

LOG_FILE = "migration.log"

def check_status():
    if not os.path.exists(LOG_FILE):
        print("❌ Log file not found. Is the script running?")
        return

    with open(LOG_FILE, "r") as f:
        lines = f.readlines()

    total_lines = len(lines)
    last_lines = lines[-10:]
    
    # Try to find the last processed item
    last_item = "Unknown"
    progress = "Unknown"
    
    for line in reversed(lines):
        if "🔄" in line:
            last_item = line.strip()
            # Extract progress [X/Y]
            match = re.search(r"\[(\d+)/(\d+)\]", line)
            if match:
                current = int(match.group(1))
                total = int(match.group(2))
                percent = (current / total) * 100
                progress = f"{current}/{total} ({percent:.1f}%)"
            break
            
    print("\n📊 Migration Status Summary")
    print("=" * 50)
    print(f"📄 Log File Size: {total_lines} lines")
    print(f"📈 Progress: {progress}")
    print(f"🔄 Last Processed: {last_item}")
    print("-" * 50)
    print("📝 Last 5 Log Entries:")
    for line in last_lines[-5:]:
        print(f"   {line.strip()}")
    print("=" * 50)
    
    # Check if process is running
    print("\n🔍 Process Check:")
    os.system("ps aux | grep '[m]igrate_to_autods.py'")

if __name__ == "__main__":
    check_status()
