#!/usr/bin/python
import os, argparse, re
from mineHeaderDataLogs import getRun, getFileId

debug = False

class RunLogs:
    def __init__(self):
        self.runlogs = []
    def getRunLog(self, run):
        for log in self.runlogs:
            if log.run == run: return log
        return None
    def add(self,runlog):
        self.runlogs.append(runlog)
    def getRuns(self):
        r = []
        for runlog in self.runlogs: r.append(runlog.run)
        return r
    def getNevents(self,run):
        n = 0
        for runlog in self.runlogs:
            if runlog.run == run:
                for log in runlog.logs:
                    n += log.Nevents
        return n
    def getNbad(self,run):
        n = 0
        for runlog in self.runlogs:
            if runlog.run == run:
                for log in runlog.logs:
                    n += log.Nbad
        return n

    
class RunLog:
    def __init__(self,run):
        self.run = run
        self.logs = []
    def add(self,log):
        self.logs.append(log)

class Log:
    def __init__(self,run,fileId):
        self.run = run
        self.fileId = fileId
        self.Nevents = -1
        self.Nbad = -1
        self.Nheaders = -1
    def toString(self):
        return 'run %d fileId %d Nevents %d NBadEvents %d Nheaders %d' % (self.run, self.fileId, self.Nevents, self.Nbad, self.Nheaders)


def analyze():

    logs = []
    for root, dirs, files in os.walk(args.directory, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            if args.r != None:
                if re.match(args.r,os.path.basename(filename)) == None:
                    if args.debug: print 'no match ' , filename
                    continue
            if args.test: print filename
            else: logs.append( analyzeLogFile(filename) )
        #for name in dirs:
        #    print(os.path.join(root, name))

    print 'Got  ', len(logs), ' log files'

    runlogs = RunLogs()
    for log in logs:
        runlog = runlogs.getRunLog(log.run)
        if runlog == None:
            runlog = RunLog(log.run)
            runlogs.add(runlog)
        runlog.add(log)

    print 'Statistics for ', len(runlogs.runlogs), ' run logs:'
    runs = runlogs.getRuns()
    print '%5s %8s %11s' % ('run','Nevents','NbadEvents')
    for run in runs:
        print '%5d %8d %11d' % (run,runlogs.getNevents(run),runlogs.getNbad(run))

    
        
            
    
    
    
def analyzeLogFile(filename):

    print 'process ', filename
    run = getRun(filename)
    fileId = getFileId(filename)
    if args.debug: print 'run ', run

    log = Log(run, fileId)
    

    f = open(filename,'r')

    lines = list(reversed( f.readlines()))

    if args.debug: print len(lines), ' lines in log file'

    for lineraw in lines:
        # match this line
        line = lineraw.rstrip()
        m = re.match('.*\snEventsProcessed\s(\d+).*',line)
        if m != None:
            log.Nevents = int(m.group(1))
            break
        m = re.match('.*\snEventsProcessedHeaderBad\s(\d+).*',line)
        if m != None:
            log.Nbad = int(m.group(1))
        m = re.match('.*\snRceSvtHeaders\s(\d+).*',line)
        if m != None:
            log.Nheaders = int(m.group(1))
    
    if args.debug:
        print 'got log ', log.toString() , ' from ', os.path.basename(filename)
    f.close()
    return log

if __name__ == '__main__':
    print 'just go'


    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--directory', required=True ,help='Directory to scan for log files')
    parser.add_argument('-r',required=False ,help='regexp in log file name')
    parser.add_argument('--debug', action='store_true',help='debug')
    parser.add_argument('--test', action='store_true',help='only test')
    parser.add_argument('-n', type=int, default=-1, help='restrict nr')
    args = parser.parse_args()
    print args
    
    debug = args.debug

    analyze()




