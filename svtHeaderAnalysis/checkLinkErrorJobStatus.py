import os, re, subprocess, argparse, sys

parser = argparse.ArgumentParser()
#parser.add_argument('d', required=True,help='File directory.')
parser.add_argument('-e', action='store_true',help='Show only runs with errors')
parser.add_argument('-n', action='store_true',help='Show only runs with no result')
args = parser.parse_args()
print args







def gettailfilepath(filepath):
    proc = subprocess.Popen('mktemp',stdout=subprocess.PIPE)
    f = proc.stdout.read()
    fp = f.rsplit()[0]
    cmd = 'tail -n 100 ' + filepath + " > " + fp
    #print cmd
    subprocess.call(cmd, shell=True)
    if not os.path.isfile(fp):
        print fp , ' is not a file?'
    return fp
    


class Log:
    def __init__(self):
        self.run = -1
        self.logfile = None
        self.eviofile = None
        self.nevents = -1
        self.nbadevents = -1
        self.syncError = False
        self.readError = False
        self.countError = False
    
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
                m = re.match('.*nEventsProcessed\s(\d+).*',l)
                if m != None: n = int(m.group(1))
                m = re.match('.*nEventsProcessedHeaderBad\s(\d+).*',l)
                if m != None: nb = int(m.group(1))
                m = re.match('.*SyncError.*',l)
                if m != None: log.syncError = True
                m = re.match('.*SvtEvioHeaderApvReadErrorException.*',l)
                if m != None: log.readError = True
                m = re.match('.*SvtEvioHeaderApvFrameCountException.*',l)
                if m != None: log.countError = True
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



# find expected list of files
filedir = '/nfs/slac/g/hps3/users/phansson/data/engrun/evio/LastFilePerRun'
logdir = '/nfs/slac/g/hps2/phansson/software/batch/output/headerAnalysis/svtHeaderAnaLastFile/data'

print 'File dir \"', filedir,'\"'

filelist = []
for f in os.listdir(filedir):
    if os.path.isfile(os.path.join(filedir,f)):
        filelist.append(os.path.join(filedir,f))

print 'Found ', len(filelist), ' files/runs:'

logs = Logs()


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

print 'Found ', len(logs.logs), ' runs'

logs.logs.sort(key=lambda x:x.run)

nruns = 0
runserr = {}
runserrall = {}
loglocked = []

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
        nruns += 1
        # list runs with error on all events
        if log.nevents == log.nbadevents:
            # these should have a locked error
            if not log.syncError and not log.readError and not log.countError:
                print 'why did it lock up?: ', log.logfile
                sys.exit(1)
            # find evio file nr for this case
            i = -1
            m = re.match('.*hps_00\d+\.evio\.(\d+).*',os.path.basename(log.logfile))
            if m != None: i = int( m.group(1) ) 
            runserrall[log.run] = i
        else:
            # list of all runs with any error 
            if log.nbadevents > 0:
                if not log.run in runserr: runserr[log.run] = [0,0]
                runserr[log.run][0] += log.nevents
                runserr[log.run][1] += log.nbadevents
                #if log.syncError or log.readError or log.countError:
                #    loglocked.append(log)
            
            
    if args.e and log.nbadevents<=0:
        continue
    if args.n and log.nevents>=0:
        continue

    
    
    print '%5d %10d %10d %15s %15s %s' % (log.run,log.nevents,log.nbadevents,evioS,logS,logF)
    

print '--> Summary <--'
print 'Runs with results: ', nruns
print 'Runs with any errors: ', len(runserr)
print 'Runs with errors on all events (locked up): ', len(runserrall)



print 'Runs with error on some but not all events and no locking error:'
countsTot = [0,0]
for r,counts in runserr.iteritems():
    if not r in runserrall:
        frac = -1.0
        if counts[0] != 0: frac = float(counts[1])/counts[0]
        print '%5d %10d %10d %10f' % (r,counts[0],counts[1],frac)
        countsTot[0] += counts[0]
        countsTot[1] += counts[1]
fracTot = -1.0
if countsTot[0] != 0: fracTot = float(countsTot[1])/countsTot[0]
print '%5s %10d %10d %10f' % ('Total',countsTot[0],countsTot[1],fracTot)

print 'Runs where we locked up and the log file:'
for log in loglocked:
    print '%5d %10d %10d %s' % (log.run,log.nevents,log.nbadevents,log.logfile)



print 'Runs and file with error on all events:'
for r,i in runserrall.iteritems():
    print r, ' ', i

    






                 



