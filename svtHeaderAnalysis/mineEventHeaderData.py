#!/usr/bin/python
import os, argparse, re, subprocess
from mineHeaderDataLogs import getRun, getFileId

debug = False

def gettailfilepath(filepath):
    proc = subprocess.Popen('mktemp /tmp/tmp.XXXXX',stdout=subprocess.PIPE,shell=True)
    f = proc.stdout.read()
    fp = f.rsplit()[0]
    cmd = 'tail -n 100 ' + filepath + " > " + fp
    #print cmd
    subprocess.call(cmd, shell=True)
    if not os.path.isfile(fp):
        print fp , ' is not a file?'
    return fp


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
    def getErrors(self,run):
        for log in self.runlogs:
            if log.run == run: return log.errors
        return None
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
        self.errors = []
    def add(self,log):
        self.logs.append(log)

class Log:
    def __init__(self,run,fileId,filepath):
        self.run = run
        self.fileId = fileId
        self.filepath = filepath
        self.Nevents = -1
        self.Nbad = -1
        self.Nheaders = -1
    def toString(self):
        return 'run %d fileId %d Nevents %d NBadEvents %d Nheaders %d' % (self.run, self.fileId, self.Nevents, self.Nbad, self.Nheaders)


class DaqError:
    def __init__(self,run,event,errortype,roc,feb,hybrid,apv):
        self.run = run
        self.event = event
        self.errortype = errortype
        self.roc = roc
        self.feb = feb
        self.hybrid = hybrid
        self.apv = apv



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
    print '%5s %8s %11s %s' % ('run','Nevents','NbadEvents','filepaths')
    for run in runs:
        paths = ''
        for log in runlogs.getRunLog(run).logs: paths += log.filepath + ','
        print '%5d %8d %11d %s' % (run,runlogs.getNevents(run),runlogs.getNbad(run),paths)


    # process errors
    if args.checkerrors:
        for runlog in runlogs.runlogs:
            runlog.errors = analyzeLogFileErrors(runlog)

    print 'Error statistics for ', len(runlogs.runlogs), ' run logs:'
    runs = runlogs.getRuns()
    print '%5s %8s %11s %8s %20s %20s' % ('run','Nevents','NbadEvents','Nerrors','ROC w/ errors','Errortypes/counts')
    for run in runs:
        errors = runlogs.getErrors(run)
        nerrors = 0
        rocs = []
        str_types = ''
        for es in errors:
            str_types += es.type + '/' + str(len(es.loc)) + ','
            nerrors += len(es.loc)
            for apv in es.loc:
                if apv.roc not in rocs: rocs.append(apv.roc)
        str_rocs = ''
        for roc in rocs: str_rocs += str(roc) + ','
        
        print '%5d %8d %11d %8d %20s %20s' % (run,runlogs.getNevents(run),runlogs.getNbad(run),nerrors,str_rocs,str_types)


    types = []
    for run in runs:
        errors = runlogs.getErrors(run)
        for e in errors:
            if not e.type in types: types.append(e.type)

    print 'Found total of ', len(types), ' errors among the runs'

    print 'Information on each error'
    for t in types:
        print '--> ', t, ' <--'
        runlist = []
        rocs = {}
        febs = {}
        for run in runs:

            
            errors = runlogs.getErrors(run)

            if args.debug: print 'run ', run, ' has ', len(errors), ' error summaries'

            for e in errors:

                if args.debug: print 'check error summary ', e.type

                if e.type == t:
                    if args.debug: print 'process error summary ', e.type, ' with ', len(e.loc), ' errors'

                    if not run in runlist: runlist.append(run)

                    if not e.roc in rocs:
                        rocs[e.roc] = []
                    if not e.feb in rocs[e.roc]: rocs[e.roc].append(e.feb)

                    if not e.feb in febs:
                        febs[e.feb] = []
                    if not e.hybrid in febs[e.feb]: febs[e.feb].append(e.hybrid)
        
        print 'runs        ', runlist
        print 'rocs:febs   ', rocs
        print 'feb:hybrids ', febs


            

class Apv:
    def __init__(self,roc,feb,hybrid,apv):
        self.roc = roc
        self.feb = feb
        self.hybrid = hybrid
        self.apv = apv

class ErrSum:
    def __init__(self,t):
        self.type = t
        self.loc = []
    def add(self,roc,feb,hybrid,apv):
        self.loc.append(Apv(roc,feb,hybrid,apv))

            
    
def analyzeLogFile(filename):

    print 'process ', filename
    run = getRun(filename)
    fileId = getFileId(filename)
    if args.debug: print 'run ', run

    log = Log(run, fileId, filename)

    fp = gettailfilepath(filename)

    #f = open(filename,'r')
    f = open(fp,'r')

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


        

def analyzeLogFileErrors(runlog):

    if args.debug: print 'Get log file errors for  ', len(runlog.logs), ' log files in run ', runlog.run

    nbad = 0
    for log in runlog.logs: nbad += log.Nbad
    if nbad== 0:
        if args.debug: print ' no errors found'
        return
    if args.debug: print ' found ', nbad, ' errors'

    #errors = []
    error_summaries = []
    for log in runlog.logs:
        filename = log.filepath

        with open(filename,'r') as f:
            for lineraw in f:
                # match this line
                line = lineraw.rstrip()
                #SvtHeaderAnalysisDriver INFO: Run 5579 event 41403468 Exception type SvtEvioHeaderApvFrameCountException for roc 57 feb 4 hybrid
                m = re.match('SvtHeaderAnalysisDriver\s.*Run\s(\d+)\sevent\s(\d+)\sException type\s(\S+)\s.*roc\s(\d+)\sfeb\s(\d+)\shybrid\s(\d+)\sapv\s(\d+).*',line)
                if m != None:
                    run = int(m.group(1))
                    event = int(m.group(2))
                    errortype = m.group(3)
                    roc = int(m.group(4))
                    feb = int(m.group(5))
                    hybrid = int(m.group(6))
                    apv = int(m.group(7))
                    error = DaqError(run,event,errortype,roc,feb,hybrid,apv)
                    #errors.append(error)
                    summary = None
                    for es in error_summaries:
                        if es.type == errortype:
                            summary = es
                    if summary == None:                     
                        summary = ErrSum(errortype)
                        error_summaries.append(summary)
                    summary.add(roc,feb,hybrid,apv)
    
    #if args.debug:
    #print 'found ', len(errors), ' errors from run ', runlog.run
    print 'found ', len(error_summaries), ' error summaries from run ', runlog.run
    return error_summaries



if __name__ == '__main__':
    print 'just go'


    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--directory', required=True ,help='Directory to scan for log files')
    parser.add_argument('-r',required=False ,help='regexp in log file name')
    parser.add_argument('--debug', action='store_true',help='debug')
    parser.add_argument('--test', action='store_true',help='only test')
    parser.add_argument('--checkerrors','-c', action='store_true',help='do error analysis')
    parser.add_argument('-n', type=int, default=-1, help='restrict nr')
    args = parser.parse_args()
    print args
    
    debug = args.debug

    analyze()




