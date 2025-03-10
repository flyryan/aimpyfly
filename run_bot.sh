#!/bin/bash
# Script to run the AIM bot with different modes

# Default values
MODE="blocking"
LOG_LEVEL="INFO"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --streaming)
      MODE="streaming"
      shift
      ;;
    --blocking)
      MODE="blocking"
      shift
      ;;
    --debug)
      LOG_LEVEL="DEBUG"
      shift
      ;;
    --info)
      LOG_LEVEL="INFO"
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --streaming    Run the bot in streaming mode"
      echo "  --blocking     Run the bot in blocking mode (default)"
      echo "  --debug        Set log level to DEBUG"
      echo "  --info         Set log level to INFO (default)"
      echo "  --help         Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Set environment variables
export API_MODE="$MODE"
export LOG_LEVEL="$LOG_LEVEL"

echo "Starting AIM bot with mode: $MODE, log level: $LOG_LEVEL"

# Run the bot
python3 run_local.py