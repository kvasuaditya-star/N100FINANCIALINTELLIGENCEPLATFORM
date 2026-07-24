import os
import sys
import time
import datetime
from pathlib import Path
import subprocess

# Setup dynamic paths
BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
ETL_SCRIPT = SCRIPTS_DIR / "etl_pipeline.py"

def run_etl():
    print(f"[{datetime.datetime.now()}] Triggering ETL Pipeline...")
    try:
        # Run the etl_pipeline.py as a subprocess
        result = subprocess.run([sys.executable, str(ETL_SCRIPT)], capture_output=True, text=True, check=True)
        print(result.stdout)
        print(f"[{datetime.datetime.now()}] ETL Pipeline run completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.datetime.now()}] ETL Pipeline failed with error:")
        print(e.stderr)
    except Exception as e:
        print(f"[{datetime.datetime.now()}] Exception occurred during ETL run: {e}")

def get_seconds_until_next_run():
    now = datetime.datetime.now()
    # Next run is weekday at 8 PM (20:00)
    target_time = now.replace(hour=20, minute=0, second=0, microsecond=0)
    
    # If it's already past 8 PM today, target is tomorrow
    if now >= target_time:
        target_time += datetime.timedelta(days=1)
        
    # Keep adding days until we get a weekday (Monday=0 to Friday=4)
    while target_time.weekday() > 4: # 5 is Saturday, 6 is Sunday
        target_time += datetime.timedelta(days=1)
        
    delta = target_time - now
    return delta.total_seconds(), target_time

def main():
    print("=" * 70)
    print("     MUTUAL FUND ETL SCHEDULER (WEEKDAY 8:00 PM)    ")
    print("=" * 70)
    print(f"ETL Script Target: {ETL_SCRIPT}")
    print(f"Current System Time: {datetime.datetime.now()}")
    
    # Check if run once option is passed
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        run_etl()
        return

    print("\n--- Windows Task Scheduler Setup Instructions ---")
    print("To run this task in the background automatically on Windows (equivalent to cron):")
    print("1. Open Windows 'Task Scheduler'.")
    print("2. Click 'Create Basic Task...'.")
    print("3. Name it 'Bluestock_MF_ETL_Pipeline'.")
    print("4. Set Trigger to 'Weekly' -> Select Monday, Tuesday, Wednesday, Thursday, Friday.")
    print("5. Set Start Time to 8:00 PM (20:00).")
    print("6. Set Action to 'Start a Program'.")
    print(f"7. Program/Script: {sys.executable}")
    print(f"8. Add Arguments: \"{ETL_SCRIPT}\"")
    print("-------------------------------------------------\n")

    print("Starting background scheduler loop...")
    while True:
        seconds_to_wait, next_run = get_seconds_until_next_run()
        print(f"\n[{datetime.datetime.now()}] Next scheduled run: {next_run}")
        print(f"Sleeping for {seconds_to_wait:.1f} seconds (~{seconds_to_wait / 3600:.2f} hours)...")
        
        # Sleep in chunks to allow Ctrl+C interrupts
        slept = 0
        chunk = 10
        try:
            while slept < seconds_to_wait:
                time.sleep(min(chunk, seconds_to_wait - slept))
                slept += chunk
        except KeyboardInterrupt:
            print("\nScheduler stopped by user.")
            break
            
        # Run ETL
        run_etl()

if __name__ == "__main__":
    main()
