#!/bin/bash


declare -a half=("top" "bot")

for i in {1..17}; do 
    r="SVT:bias:top:$i:v_sens";
    echo $r;
    myget -c "$r" -b -100w > "$r.mya" 
done


for i in {20..37}; do 
    r="SVT:bias:bot:$i:v_sens";
    echo $r;
    myget -c "$r" -b -100w > "$r.mya" 
done


