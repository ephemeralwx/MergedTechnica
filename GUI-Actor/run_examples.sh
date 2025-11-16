#!/bin/bash
# Example commands for the autonomous GUI agent

echo "🤖 Autonomous GUI Agent - Example Commands"
echo "=========================================="
echo ""
echo "Choose an example:"
echo "1. Open Safari"
echo "2. Open Finder"
echo "3. Open System Settings"
echo "4. Custom goal"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo "Running: Open Safari"
        python main.py "Open Safari"
        ;;
    2)
        echo "Running: Open Finder"
        python main.py "Open Finder"
        ;;
    3)
        echo "Running: Open System Settings"
        python main.py "Open System Settings"
        ;;
    4)
        read -p "Enter your goal: " goal
        python main.py "$goal"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
