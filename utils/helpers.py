import subprocess
import time

from db import db, get_cursor


# =============================
# RUN COMMAND
# =============================
def run_command(cmd):

    print(
        f"RUNNING: {cmd}",
        flush=True
    )

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )

    print(
        f"RETURN CODE: {result.returncode}",
        flush=True
    )

    print(
        f"STDOUT: {result.stdout}",
        flush=True
    )

    print(
        f"STDERR: {result.stderr}",
        flush=True
    )

    return result


# =============================
# WAIT BEFORE FIX
# =============================
def wait_before_fix(seconds=10):

    print(
        f"Waiting {seconds}s before fix",
        flush=True
    )

    time.sleep(seconds)


# =============================
# SAVE ACTION TO POSTGRES
# =============================
def save_action(alert_name, action, status):

    try:

        cursor = get_cursor()

        query = """
        INSERT INTO action_history
        (
            event_time,
            alert_name,
            action_taken,
            status
        )
        VALUES (%s, %s, %s, %s)
        """

        values = (
            time.strftime("%Y-%m-%d %H:%M:%S"),
            alert_name,
            action,
            status
        )

        cursor.execute(
            query,
            values
        )

        db.commit()

        print(
            "Action stored in PostgreSQL",
            flush=True
        )

    except Exception as e:

        print(
            "DB save error:",
            e,
            flush=True
        )
