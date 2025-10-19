#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Letta Chat Client - Main Entry Point
Simple text-based chat interface

Copyright (C) 2024 AnimusUNO

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import argparse
import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from simple_chat import main
from tui_app import run as run_tui

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Letta Chat Client')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging output')
    parser.add_argument('--debug', '-d', action='store_true',
                       help='Enable debug logging output')
    parser.add_argument('--reasoning', '-r', action='store_true',
                       help='Show agent reasoning/thinking process')
    parser.add_argument('--text', '-t', action='store_true',
                       help='Use original text interface instead of TUI')
    
    args = parser.parse_args()
    
    try:
        if args.text:
            # Use original text interface when requested
            asyncio.run(main(verbose=args.verbose, debug=args.debug, reasoning=args.reasoning))
        else:
            # Use enhanced TUI by default - pass reasoning flag
            run_tui(reasoning=args.reasoning)
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
