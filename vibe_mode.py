#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Autonomous Vibe Mode Script

Runs in the background and periodically sends the VIBE_MODE_PROMPT to the
currently selected agent using the existing letta_client. Controlled by a
JSON control file to start/stop gracefully.
"""
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure local imports resolve when launched from project root
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from letta_api import letta_client


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _control_path() -> Path:
    return Path(config.vibe_control_file)


def _read_state() -> dict:
    path = _control_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_state(state: dict) -> None:
    path = _control_path()
    try:
        path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception:
        pass


def _setup_logging() -> None:
    log_path = Path(config.vibe_log_file)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            # no console handler to stay quiet when backgrounded
        ],
    )


_stop_flag = False


def _signal_handler(signum, frame):  # noqa: ARG001
    global _stop_flag
    _stop_flag = True


def main() -> int:
    if not config.validate():
        print("Config invalid; exiting vibe_mode.")
        return 1

    _setup_logging()
    logging.info("Vibe mode script started")

    # Register signal handlers for graceful shutdown
    try:
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)
    except Exception:
        # Not all platforms support signals equally; proceed best-effort
        pass

    # Initialize control state
    state = _read_state()
    state.update({
        "status": "running",
        "last_command": "start",
        "timestamp": _now_iso(),
        "pid": os.getpid(),
    })
    _write_state(state)

    interval = max(10, int(config.vibe_interval_seconds))  # minimum 10s safety

    while not _stop_flag:
        # Check control file for stop
        current = _read_state()
        if current.get("last_command") == "stop" or current.get("status") == "stopped":
            logging.info("Stop command detected; exiting.")
            break

        # Ensure an agent is selected
        agent_id = getattr(letta_client, "current_agent_id", None)
        if not agent_id:
            logging.warning("No agent selected; skipping this cycle.")
        else:
            try:
                logging.info("Sending vibe prompt to agent %s", agent_id)
                # Stream and consume to completion (log a short preview)
                preview = []
                async_gen = letta_client.send_message_stream(config.vibe_mode_prompt, show_reasoning=False)
                # Consume the async generator from a synchronous context
                # by running a tiny event loop per cycle
                import asyncio

                async def _drain():
                    count = 0
                    async for chunk in async_gen:
                        if isinstance(chunk, str) and not chunk.startswith("__REASONING__:"):
                            if len(preview) < 5:
                                preview.append(chunk)
                        count += 1
                    return count

                count = asyncio.run(_drain())
                logging.info("Response received (chunks=%s) preview=%.120s", count, "".join(preview).replace("\n", " "))
            except Exception as e:
                logging.error("Error sending vibe prompt: %s", e)

        # Update control file timestamps
        state = _read_state()
        state.update({
            "status": "running",
            "last_run": _now_iso(),
            "pid": os.getpid(),
        })
        _write_state(state)

        # Sleep until next interval, with early exit if stop is requested
        for _ in range(interval):
            if _stop_flag:
                break
            # re-check control file every second
            if _read_state().get("last_command") == "stop":
                _stop_flag = True
                break
            time.sleep(1)

    # Mark stopped
    state = _read_state()
    state.update({
        "status": "stopped",
        "last_command": "stop",
        "timestamp": _now_iso(),
    })
    _write_state(state)
    logging.info("Vibe mode script stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



