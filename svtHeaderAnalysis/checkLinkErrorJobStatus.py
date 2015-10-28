import os, re, subprocess, argparse

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

    if args.e and log.nbadevents<=0:
        continue
    if args.n and log.nevents>=0:
        continue
    
    print '%5d %10d %10d %15s %15s %s' % (log.run,log.nevents,log.nbadevents,evioS,logS,logF)
    




# find the log files for each run
#loglist = {}
#for run,eviofile in runlist.iteritems():
#    log = None
#    for f in os.listdir(logdir):
#        m = re.match('hps.*00' +str(run)+'\.evio\.(\d+).*headerAnaLast',os.path#.basename(f))
#        if m != None:
#            print 'matched log ', f, ' run ', m.group(1)
#            # find the text file itself
#            for ff in os.listdir(os.path.join(logdir,f)):
#                m = re.match('hps.*00(\d+)\.evio\.(\d+).log.1',os.path.basename(ff))
#                log = os.path.join(os.path.join(logdir,f),ff)
#        else:
#            print ' no log match for ', f
#    if run in loglist:
#        loglist[run] = log
#
#
#print 'found ', len(loglist), ' logs:'
#print '%5s %15s %15s %s' % ('run','logfilesize','eviosize','logfile')
#for k,v in loglist.iteritems():
#
#    if v == None:
#        print '%5d %15s %15s %s' % (k, 'No log file',', '-')
#    elif os.path.getsize(v) == None:
#        print '%5d %15s %s' % (k, 'Empty log file','-')
#    else:
#        print '%5d %15d %s' % (k, os.path.getsize(v), v)



                 



