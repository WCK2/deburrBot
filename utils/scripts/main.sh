PYTHONPATH=/home/jakauser/lib/python
export PYTHONPATH
LD_LIBRARY_PATH=$PYTHONPATH/jaka/jkrc
export LD_LIBRARY_PATH


MY_DIR=/home/jakauser/repos/deburrBot
cd $MY_DIR

# screen -wipe
TIMESTAMP=$(date +"%Y_%m_%d_%H_%M_%S")
LOG_FILE="$MY_DIR/assets/logs/robot_$TIMESTAMP.log"

python3 -u main.py | while IFS= read -r line; do printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$line"; done | tee $LOG_FILE
#python3 -u main.py


# Notes
    # create shell script using nano (do not transfer using filezilla)
    # chmod 777 both shell scripts and main python program