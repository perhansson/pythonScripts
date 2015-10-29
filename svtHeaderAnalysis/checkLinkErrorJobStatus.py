import os, re, subprocess, argparse, sys

parser = argparse.ArgumentParser()
#parser.add_argument('d', required=True,help='File directory.')
parser.add_argument('-e', action='store_true',help='Show only runs with errors')
parser.add_argument('-n', action='store_true',help='Show only runs with no result')
parser.add_argument('--logdir', help='Directory of log files')
parser.add_argument('--checkevio', action='store_true', help='Check and use EVIO files')
args = parser.parse_args()
print args







def gettailfilepath(filepath):
    """Find tail lines of a file"""
    proc = subprocess.Popen('mktemp /tmp/tmp.XXXXX',stdout=subprocess.PIPE,shell=True)
    f = proc.stdout.read()
    fp = f.rsplit()[0]
    cmd = 'tail -n 100 ' + filepath + " > " + fp
    subprocess.call(cmd, shell=True)
    if not os.path.isfile(fp):
        print fp , ' is not a file?'
    return fp
    

class DaqErrorSummary:
    def __init__(self,name, rocs):
        self.name = name
        self.rocs = rocs



class Log:
    def __init__(self):
        self.run = -1
        self.logfile = None
        self.eviofile = None
        self.nevents = -1
        self.nbadevents = -1
        self.errors = []
    def __eq__(self, other):
        if self.run == other.run and self.logfile == other.logfile:
            return True
        else:
            return False
    def __neq__(self,other):
        if self.__eq__(other):
            return False
        else:
            return True
    def __hash__(self):
        return hash(0)
    
    def processTail(self):
        # find the end of run
        if self.logfile == None:
            return
        filepath = gettailfilepath(self.logfile)
        f = open(filepath,'r')
        if f == None:
            self.nevents = -2
            self.nbadevents = -2
        else:
            n = -3
            nb = -3
            for line in f.readlines():
                l = line.rsplit('\n')[0]
                # find number of events in this log file
                m = re.match('.*nEventsProcessed\s(\d+).*',l)
                if m != None: n = int(m.group(1))
                # find number of events with errors in this log file
                m = re.match('.*nEventsProcessedHeaderBad\s(\d+).*',l)
                if m != None: nb = int(m.group(1))
                # find the summary of errors happened in this log file 
                # I do this in two steps but I'm sure one can do it with regexp...
                m = re.match('SvtHeaderAnalysisDriver INFO:\s(\w+)\s(\d+)\s.*individual roc counts\s(\d+):(\d+).*',l)
                if m != None:
                    name = m.group(1)
                    roc_count = int(m.group(2))
                    rocs = {}
                    # now find the individual rocs
                    for roc_count in l.split('roc counts ')[1].split(')')[0].split():
                        rocs[ int( roc_count.split(':')[0] ) ] = int( roc_count.split(':')[1] )
                    self.errors.append(DaqErrorSummary(name,rocs))
            self.nevents = n
            self.nbadevents = nb
        f.close()


class Logs:
    def __init__(self):
        self.logs = []
    def has(self,log):
        for l in self.logs:
            if log.run == l.run:
                return True
        return False
    def add(self,log):
        self.logs.append(log)


def getEvioFileList(filedir):

    # find expected list of files

    print 'File dir \"', filedir,'\"'

    filelist = []
    for f in os.listdir(filedir):
        if os.path.isfile(os.path.join(filedir,f)):
            filelist.append(os.path.join(filedir,f))

    return filelist

def getLogs(filelist, logdir):
    logs = Logs()
    if filelist != None:
        print 'Find logs via evio files'
        for f in filelist:
            m = re.match('hps.*00(\d+)\.evio\.(\d+)',os.path.basename(f))
            if m != None:
                #print 'matched ', f, ' run ', m.group(1)
                run = int(m.group(1))
                logfile = None
                for lf in os.listdir(logdir):
                    lm = re.match('hps.*00' +str(run)+'\.evio\.(\d+).*',os.path.basename(lf))
                    if lm != None:
                        #print 'matched log ', lf, ' run ', run
                        # find the text file itself
                        for lff in os.listdir(os.path.join(logdir,lf)):
                            lmm = re.match('hps.*00(\d+)\.evio\.(\d+)\.log\.1',os.path.basename(lff))
                            if lmm !=None:
                                logfile = os.path.join(os.path.join(logdir,lf),lff)

                log = Log()
                log.run = run
                log.eviofile = f
                log.logfile = logfile
                logs.add(log)
    else:
        print 'look at log files directly'
        for lf in os.listdir(logdir):
            lm = re.match('hps_00(\d+)\.evio\.(\d+).*',os.path.basename(lf))
            if lm != None:
                logfile = None
                run = int(lm.group(1))
                #print 'matched log ', lf, ' run ', run
                # find the text file itself
                for lff in os.listdir(os.path.join(logdir,lf)):
                    lmm = re.match('hps.*00' + str(run) + '\.evio\.(\d+)\.log\.1',os.path.basename(lff))
                    if lmm !=None:
                        logfile = os.path.join(os.path.join(logdir,lf),lff)

                log = Log()
                log.run = run
                #log.eviofile = '-'
                log.logfile = logfile
                logs.add(log)

    return logs


filedir = '/nfs/slac/g/hps3/users/phansson/data/engrun/evio/LastFilePerRun'
logdir = '/nfs/slac/g/hps2/phansson/software/batch/output/headerAnalysis/svtHeaderAnaLastFile/data'

if args.logdir != None:
    logdir = args.logdir

filelist = []
logs = None

if args.checkevio:
    print 'Find logs via evio files'
    filelist = getEvioFileList(filedir)
    logs = getLogs(filelist,logdir)
else:
    logs = getLogs(None,logdir)
    

print 'Found ', len(filelist), ' files/runs:'
print 'Found ', len(logs.logs), ' runs'

logs.logs.sort(key=lambda x:x.run)

runschecked = []
runslocked = []
runserr = []
runsgood = []

print '%5s %10s %10s %15s %15s %s' % ('run','Nevents','Nbadevents','eviofilesize','logfilesize','logfile')
for log in logs.logs:

    if log.eviofile == None: evioS = 'None'
    else: evioS = str(os.path.getsize(log.eviofile))
    
    if log.logfile == None:
        logS = 'None'
        logF = '-'
    else:
        logS = str(os.path.getsize(log.logfile))
        logF = log.logfile

    log.processTail()

    # pick out logs and count
    # only do it for those that had some events
    if log.nevents > 0:

        runschecked.append(log)

        # list runs with error on all events
        if log.nevents == log.nbadevents:
            # these should have a locked error
            #if not log.syncError and not log.readError and not log.countError:
            #    print 'why did it lock up?: ', log.logfile
            #    sys.exit(1)
            runslocked.append(log)
        elif log.nbadevents > 0:
            # list of all runs with any error but not on all events
            runserr.append(log)
            #if l == log:
            #    runserr[log.run][0] += log.nevents
            #    runserr[log.run][1] += log.nbadevents
            #    #if log.syncError or log.readError or log.countError:
            #    #    loglocked.append(log)
        else:
            # list all that are ok
            runsgood.append(log)
            
    if args.e and log.nbadevents<=0:
        continue
    if args.n and log.nevents>=0:
        continue

    
    
    print '%5d %10d %10d %15s %15s %s' % (log.run,log.nevents,log.nbadevents,evioS,logS,logF)
    

print '--> Summary <--'
print 'Runs with results               : ', len(runschecked)
print 'Runs without any errors         : ', len(runsgood)
print 'Runs w/ error but not locked up : ', len(runserr)
print 'Runs locked up                  : ', len(runslocked)



print '\nMore details on each category\n'

print 'Runs w/ error but not locked up : ', len(runserr)
print '%5s %10s %10s %10s %10s' % ('run','nEvents','nBadEvents','fractionBad','Errors')
countsTot = [0,0]
for log in runserr:
    counts = [log.nevents, log.nbadevents]
    frac = -1.0
    if counts[0] != 0: frac = float(counts[1])/counts[0]
    error_names = ''
    for error in log.errors: error_names += error.name + ','
    print '%5d %10d %10d %10f %10s' % (log.run,counts[0],counts[1],frac,error_names)
    countsTot[0] += counts[0]
    countsTot[1] += counts[1]
fracTot = -1.0
if countsTot[0] != 0: fracTot = float(countsTot[1])/countsTot[0]
print '%5s %10d %10d %10f' % ('Total',countsTot[0],countsTot[1],fracTot)

print '\nRuns that where locked up:'
print '%5s %10s %10s %10s %30s' % ('run','nEvents','nBadEvents','evioFileId','ErrorName/roc:count')
for log in runslocked:
    # find evio file nr for this case
    i = -1
    m = re.match('.*hps_00\d+\.evio\.(\d+).*',os.path.basename(log.logfile))
    if m != None: i = int( m.group(1) ) 
    error_names = ''
    for error in log.errors:
        error_names += error.name + '/' + str(error.rocs) + ','
    print '%5d %10d %10d %10d %30s' % (log.run,log.nevents,log.nbadevents,i,error_names)

print '\nRuns that needs to be further processed:'
print '%5s %10s %s' % ('run','evioFileId','logfile')
for log in runslocked:
    # find evio file nr for this case
    i = -1
    m = re.match('.*hps_00\d+\.evio\.(\d+).*',os.path.basename(log.logfile))
    if m != None: i = int( m.group(1) ) 
    print '%5d %10d %s' % (log.run,i,log.logfile)



    






                 



