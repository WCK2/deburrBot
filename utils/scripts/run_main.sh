#!/usr/bin/env bash
. /home/jakauser/.willrc

cd /home/jakauser/repos/deburrBot

SCREEN_NAME="main"
COMMAND=". ./main.sh"

screen_stuff "$SCREEN_NAME" "$COMMAND"



# Notes
    # create shell script using nano (do not transfer using filezilla)
    # chmod 777 both shell scripts and main python program