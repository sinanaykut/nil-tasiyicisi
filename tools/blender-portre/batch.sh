#!/bin/bash
# full portrait batch: 6 moods for named characters, 3 for generic townsfolk roles
cd "$(dirname "$0")"
M6=neutral,happy,angry,sly,surprised,thinking; M3=neutral,happy,angry
for k in h_ahmose h_neferet h_sitre h_bakenre paneb sethi hapu 0 1 2 3 4 5 6 7 tv0 tv1 tv3 tv4 tv7; do SAMPLES=12 python3 char31.py $k $M6 final 320 2>&1 | grep RENDER; done
for k in priest guard scribe; do SAMPLES=12 python3 char31.py $k $M3 final 320 2>&1 | grep RENDER; done
echo DONE
