import os
import subprocess
import sys
import re

class HeaderException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)


def getRunDict(loglist):
    d = {}
    for l in loglist:
        if l.run not in d:
            d[l.run] = []
        d[l.run].append(l)
    return d

def getEvioFileList(filedir):

    # find expected list of files

    print 'File dir \"', filedir,'\"'

    filelist = []
    for f in os.listdir(filedir):
        if os.path.isfile(os.path.join(filedir,f)):
            filelist.append(os.path.join(filedir,f))

    return filelist

def getLogs(filelist, logdir):
    logs = []
    if filelist != None:
        print 'Find logs via evio files'
        for f in filelist:
            m = re.match('hps.*00(\d+)\.evio\.(\d+)',os.path.basename(f))
            if m != None:
                #print 'matched ', f, ' run ', m.group(1)
                run = int(m.group(1))
                filenr = int(m.group(2))
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
                log.filenr = filenr
                log.eviofile = f
                log.logfile = logfile
                logs.append(log)
    else:
        print 'look at log files directly from \"', logdir, '\"'
        for lf in os.listdir(logdir):
            lm = re.match('hps_00(\d+)\.evio\.(\d+).*',os.path.basename(lf))
            if lm != None:
                logfile = None
                run = int(lm.group(1))
                filenr = int(lm.group(2))
                #print 'matched log ', lf, ' run ', run
                # find the text file itself
                for lff in os.listdir(os.path.join(logdir,lf)):
                    lmm = re.match('hps.*00' + str(run) + '\.evio\.(\d+)\.log\.1',os.path.basename(lff))
                    if lmm !=None:
                        logfile = os.path.join(os.path.join(logdir,lf),lff)

                log = Log()
                log.run = run
                log.filenr = filenr
                #log.eviofile = '-'
                log.logfile = logfile
                logs.append(log)

    return logs


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
        self.filenr = -1
        self.locked = []
    def __eq__(self, other):
        if other and self.run == other.run and self.logfile == other.logfile:
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
    def __str__(self):
        s = 'Log: run ' + str(self.run) + ' filenr ' + str(self.filenr) + ' n ' + str(self.nevents) + ' logfile '
        if self.logfile: s += self.logfile
        else: s += 'None'
        
        return s

    def isLocked(self):
        if self.locked: return True
        else: return False

    def locked_str(self):
        s = []
        [s.append(str(l)) for l in self.locked]
        return s
        
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
                    # rocs find the individual rocs
                    for roc_count in l.split('roc counts ')[1].split(')')[0].split():
                        rocs[ int( roc_count.split(':')[0] ) ] = int( roc_count.split(':')[1] )
                    self.errors.append(DaqErrorSummary(name,rocs))
            self.nevents = n
            self.nbadevents = nb
        f.close()


class Logs:

    def __init__(self):
        self.logs = []

    def addList(self,listOfLogs,checkDupl):
        for l in listOfLogs:
            self.add(l,checkDupl)
    

    def add(self,log,checkDupl):
        if not checkDupl:
            self.logs.append( log )
        else:
            #print 'try to add ', log
            sellog = None
            if log not in self.logs:
                sellog = log
            else:
                otherlogs = []
                while True:
                    if log not in self.logs:
                        break
                    else:
                        index = self.logs.index( log )
                        otherlog =  self.logs.pop(index)
                        otherlogs.append( otherlog )
                if len(otherlogs) == 0:
                    raise HeaderException('the list is empty?')
                if len(otherlogs) != 1:
                    raise HeaderException('more than one duplicate?')
                # add this one to have all in one list
                otherlogs.append( log )
                # now select the one with info (should be only two?)
                for l in otherlogs:
                    if sellog == None:
                        sellog = l
                    else:
                        if sellog.nevents > 0 and l.nevents > 0:
                            raise HeaderException('I dont think this should happen!?')
                        #if sellog.nevents < 0 and l.nevents < 0:
                            #print 'Both duplicates empty?'
                            #print sellog
                            #print l
                        if sellog.nevents < 0 and l.nevents > 0:
                            sellog = l
            if sellog == None:
                raise HeaderException('couldnt find the duplicate to use')

            # push it to the list
            self.logs.append( sellog )



class Lock(object):
    '''Information about the DAQ lock'''
    def __init__(self, run, event, dateStr):
        self.run = run
        self.event = event
        self.dateStr = dateStr

class LockedLog(object):
    '''Log that had a DAQ error lock'''
    def __init__(self,log):
        self.log = log
        self.run = log.run
        self.lock = self.findLock()

    def findLock(self):
        '''Find the event where the lock happened'''
        #'SvtHeaderAnalysisDriver INFO: svt_event_header_good 0 for run 5733 event 8794087 date Sat May 16 04:44:18 PDT 2015 processed 188349'
        lock = None
        #print 'Search for lock in file ', self.log.logfile
        with open(self.log.logfile,'r') as f:
            for line in f:
                # find the line where header flag is bad
                m = re.match('.*svt_event_header_good\s(\d)\s.*run\s(\d+)\s.*event\s(\d+)\s.*date\s(.*)\sprocessed\s(\d+)', line)
                if m != None:
                    if int(m.group(1)) != 0:
                        print 'ERROR header is not bad!?'
                        sys.exit(1)
                    lock = Lock( int(m.group(2)), int(m.group(3)), m.group(4) )
                    break
        if lock == None:
            print 'ERROR: could not find a lock'
            sys.exit(1)
        #print 'found lock at event ', lock.event, ' and date ', lock.dateStr
        return lock
    

def processEventTimeFile(path_to_file):
    print 'Process event time file ', path_to_file
    lockedRunEventTimeMap = {}
    with open(path_to_file,'r') as f:
        for line in f:
            #print 'line ', line
            #run 5034 event 15738 eventtime 16942195616 eventdate Wed Dec 31 16:00:16 PST 1969
            m = re.match('.*run\s(\d+)\sevent\s(\d+)\seventtime\s(\d+)\seventdate.*',line)
            if m != None:
                run = int(m.group(1))
                evt = int(m.group(2))
                time = int(m.group(3))
                if run not in lockedRunEventTimeMap:
                    lockedRunEventTimeMap[run] = []
                if len(lockedRunEventTimeMap[run]) != 0:
                    raise HeaderException('This shouldnt happen')
                lockedRunEventTimeMap[run].append(evt)
                lockedRunEventTimeMap[run].append(time)
    return lockedRunEventTimeMap


