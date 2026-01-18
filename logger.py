import csv
import json
from datetime import datetime
from websockets.sync.client import connect

def log_data():
    print("Connecting to stream... waiting for active state to begin logging")

    csv_file = None
    writer = None
    filename = None
    message_count = 0
    is_logging = False

    try:
        with connect("ws://10.12.123.45:3333/data", open_timeout=10) as websocket:
            for message in websocket:
                try:
                    data = json.loads(message)
                    current_state = data.get('state')

                    # Check if we should start logging (leaving standby state)
                    if not is_logging and current_state != 0:
                        # Create new file with timestamp
                        filename = f"logs/telemetry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        csv_file = open(filename, mode='w', newline='')
                        writer = None
                        message_count = 0
                        is_logging = True
                        print(f"Active state detected. Started logging to {filename}")

                    # Check if we should stop logging (returning to standby state)
                    elif is_logging and current_state == 0:
                        if csv_file:
                            csv_file.close()
                            print(f"Standby state reached. Saved {message_count} messages to {filename}")
                        csv_file = None
                        writer = None
                        is_logging = False
                        continue

                    # Log data if we're in active logging mode
                    if is_logging:
                        # Flatten the data structure
                        row = {}
                        for key, value in data.items():
                            if isinstance(value, list):
                                for i, val in enumerate(value):
                                    row[f"{key}_{i}"] = val
                            else:
                                row[key] = value

                        # Initialize headers on first message of this logging session
                        if writer is None:
                            writer = csv.DictWriter(csv_file, fieldnames=row.keys())
                            writer.writeheader()

                        # Write data
                        writer.writerow(row)
                        message_count += 1

                        # Flush every 10 entries
                        if message_count % 10 == 0:
                            csv_file.flush()

                        # Optional: print status every 100 entries
                        if message_count % 100 == 0:
                            print(f"Logged {message_count} rows...")

                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"Error processing message: {e}")
                    continue

    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        # Clean up: close file if still open
        if csv_file:
            csv_file.close()
            print(f"Connection closed. Final save: {message_count} messages in {filename}")

if __name__ == "__main__":
    try:
        log_data()
    except KeyboardInterrupt:
        print("\nManual stop.")