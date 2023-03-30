#!/bin/bash
#The script is run like: ./toggleLED $SERIALNUMBER $HOSTNAME
#Checks if host can be connected to
host=$2
if ! timeout 10 ssh $host exit; then
    echo "Error: SSH connection failed"
    exit 1
fi

path=""
parsedpath=""
echo "Looking for the path..."
#Searches host for a path linked to a serial number
for i in $(timeout 10 ssh $host "ls /dev/sd*" | grep -v [0-9] ); do if (timeout 10 ssh $host smartctl -a $i | grep $1 ); then path="$i"; break; fi; done &> /dev/null
#Parses the path name to only contain the final part, i.e. sdaa
parsedpath=$(timeout 10 ssh $host echo "${path%1}" | cut -d '/' -f3)
if [ -z "$parsedpath" ]; then
    echo "Error: Path parsing failed (Path not found)"
    exit 1
fi
echo "${parsedpath} is the path"
#Checks to see if locate is set to 0 or 1, off or on respectively.
#Then, toggles the LED to be the opposite of what it currently was, i.e. turns off if it was on.
ledStatus=$(timeout 10 ssh $host "cat /sys/class/enclosure/*/*/device/block/$parsedpath/../../enclosure*/locate")
if [[ $ledStatus -eq "0" ]]; then
    echo "The drive's LED is currently turned off. Turning LED on..."
    if ! timeout 10 ssh $host "echo 1 > /sys/class/enclosure/*/*/device/block/$parsedpath/../../enclosure*/locate" ; then
        echo "Error: Failed to make drive LED blink"
        exit 1
    fi
    echo "Drive LED is now blinking. Re-enter the command again to toggle the LED off."
elif [[ $ledStatus -eq "1" ]]; then
    echo "The drive's LED is currently turned on. Turning LED off..."
    if ! timeout 10 ssh $host "echo 0 > /sys/class/enclosure/*/*/device/block/$parsedpath/../../enclosure*/locate" ; then
        echo "Error: Failed to make drive LED stop blinking"
        exit 1
    fi
    echo "Drive LED has stopped blinking. Re-enter the command again to toggle the LED on."
else
    echo "Error: Couldn't cat the path's enclosure/locate"
    exit 1
fi
