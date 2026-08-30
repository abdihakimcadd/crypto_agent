"""
Persistent scheduler for fly.io deployment.
Runs on a single lightweight machine in Singapore (sin) region.
Handles 30-min cadence for volume_cron.py and pipeline.py with 2-min offset.
No external cron needed — Python asyncio handles timing.
"""
import asyncio
import subprocess
from datetime import datetime


async def run_script(script_name: str):
    """Run a Python script and log output."""
    print(f"[{datetime.utcnow()}] Starting {script_name}...")
    result = subprocess.run(
        ["python", script_name],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print(f"ERROR in {script_name}:", result.stderr)
    print(f"[{datetime.utcnow()}] Finished {script_name}")


async def scheduler_loop():
    """Main loop: runs volume_cron at :00 and :30, pipeline 2 min after."""
    print("Scheduler started. Waiting for next 30-min boundary...")

    while True:
        now = datetime.utcnow()
        minute = now.minute
        second = now.second

        # Trigger at :00 and :30
        if minute in [0, 30] and second < 10:
            # Step 1: Volume cron
            await run_script("volume_cron.py")

            # Step 2: Wait 2 minutes for volume data to land in Supabase
            print("Waiting 2 minutes for volume data to settle...")
            await asyncio.sleep(120)

            # Step 3: Agent pipeline
            await run_script("pipeline.py")

            # Sleep until past the trigger window to avoid double-firing
            await asyncio.sleep(60)
        else:
            # Check every 10 seconds
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(scheduler_loop())
