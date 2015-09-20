#!/usr/bin/python

import os,sys,argparse,subprocess


parser = argparse.ArgumentParser()
parser.add_argument('-j',required=True,help='JAR file')
parser.add_argument('-f',required=True, nargs='+',help='Input lcio files')
parser.add_argument('-s',required=True,help='steering file')
parser.add_argument('-r',action='store_true',help='run job')
args = parser.parse_args()
print args

cmd = 'java -jar ' + args.j + ' -f ' + args.s 

for f in args.f:
    c = cmd + ' -DoutputFile=' + os.path.basename(f) + '-headerana' + ' -i ' + f
    print c
    if args.r:
        subprocess.call(c,shell=True)



#istribution/target/hps-distribution-3.4.1-SNAPSHOT-bin.jar -f ../kepler2/hps-java/steering-files/src/main/resources/org/hps/steering/users/phansson/EvioToLcio_LinkError.lcsim -DoutputFile=hps_005772.evio.0.header-ana -i hps_005772.evio.0.header.slcio



