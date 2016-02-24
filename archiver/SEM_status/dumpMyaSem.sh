#!/bin/bash



for FEB in `seq 0 9`; do
    s="SVT:daq:feb:$FEB:sem_error_stat"
    echo $s
    #caget $s
    myget -c "$s" -b -100w > "sem_error_$FEB.mya"
    s="SVT:daq:feb:$FEB:sem_heartbeat_stat"
    echo $s
    myget -c "$s" -b -100w > "sem_heartbeat_$FEB.mya"
    #caget $s
done

#declare -a half=("top" "bot")
#
#for i in {1..17}; do 
#    r="SVT:bias:top:$i:v_sens";
#    echo $r;
#    myget -c "$r" -b -100w > "$r.mya" 
#done


