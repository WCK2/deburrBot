#!/usr/bin/env bash
. /home/jakauser/.willrc

cd /home/jakauser/repos/PickPlaceWeldBot

SCREEN_NAME="main"
COMMAND=". ./main.sh"

screen_stuff "$SCREEN_NAME" "$COMMAND"

