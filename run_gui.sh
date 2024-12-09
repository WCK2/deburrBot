#!/bin/bash
PROJECT_DIR="/home/will/repos/deburrBot"
TIMESTAMP=$(date +"%Y_%m_%d_%H_%M_%S")
LOG_FILE="$PROJECT_DIR/assets/logs/gui_log_$TIMESTAMP.log"

screen -dmS wmain bash
screen -S wmain -X stuff "cd $PROJECT_DIR^M"
screen -S wmain -X stuff "python -u main.py | tee -a $LOG_FILE^M"

# screen -dmS wmain bash -c "cd $PROJECT_DIR; set +e; python -u main.py | while IFS= read -r line; do printf '[%s] %s\n' \"\$(date '+%Y-%m-%d %H:%M:%S')\" \"\$line\"; done | tee -a $LOG_FILE; exec bash"
# screen -dmS wmain bash -i -c "cd $PROJECT_DIR; python -u main.py | while IFS= read -r line; do printf '[%s] %s\n' \"\$(date '+%Y-%m-%d %H:%M:%S')\" \"\$line\"; done | tee -a $LOG_FILE"

