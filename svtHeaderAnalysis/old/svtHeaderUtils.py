import os
import subprocess


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
        errors = []
        for log in self.runlogs:
            if log.run == run:
                errors = log.errors
                break
        return errors
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



class JobSummaryCount(object):
    """ Reads in the counts at the end of the job """
    names = ['nRceSvtHeaders', 'nRceSyncErrorCountN', 'nRceOFErrorCount', 'nRceSkipCount', 'nRceMultisampleErrorCount']
    errorNames = ['nRceSyncErrorCountN', 'nRceOFErrorCount', 'nRceSkipCount', 'nRceMultisampleErrorCount']
    @staticmethod
    def matchLine(line):
        if debug: print 'trying to match \"' + '.*\s([a-z]|[A-Z]+)\s(\d+).*' + '\" to line'
        for name in JobSummaryCount.names:
            m = re.match('.*\s'+name+'\s(\d+).*',line)
            if m != None:
                if debug: print 'matched ', m.groups(), ' for ', name
                return [name, m]
        return None

    def __init__(self,run,name,n):
        self.run = run
        self.n = n
        self.name = name
    
    def toString(self):
        return 'JobSummaryCount run ' + str(self.run) + ' ' + self.name + ' ' + str(self.n)


class MultiSampleError(object):
    @staticmethod
    def matchLine(line):
        return  re.match('.*run\s(\d+)\sevent\s(\d+)\sdate\s(.*)\sroc\s(\d+)\sfeb\s(\d+)\shybrid\s(\d+)\sapv\s(\d+).*', line)

    def __init__(self,run,event,dateStr,roc,feb,hybrid,apv):
        self.run = run
        self.event = event
        self.roc = roc
        self.feb = feb
        self.hybrid = hybrid
        self.apv = apv
        self.dateStr = dateStr
    
    def toString(self):
        return 'MultisampleError ' + str(self.run) + ' ' + str(self.event) + ' ' + str(self.roc) + ' ' + str(self.feb) + ' ' + str(self.hybrid) + ' ' + str(self.apv)

class SyncError(object):
    @staticmethod
    def matchLine(line):
        return  re.match('.*syncError.*run\s(\d+).*event\s(\d+).*date.*date\s(.*)\sroc\s(\d+).*',line)
        
    def __init__(self,run,event,roc,dateString):
        self.run = run
        self.event = event
        self.roc = roc
        self.dateString = dateString
    
    def toString(self):
        return 'SyncError ' + str(self.run) + ' ' + str(self.event) + ' ' + self.dateString + ' ROC ' + str(self.roc)

    

class LogFile(object):
    def __init__(self, run):
        self.run = run
        self.multisampleErrors = []
        self.syncErrors = []
        self.jobSummaryCounts = []

    def getJobSummaryCount(self, name):
        for jsc in self.jobSummaryCounts:
            if name == jsc.name:
                return jsc
        return None

    def getErrors(self):
        jscNZ = [] # non-zero
        for errorName in JobSummaryCount.errorNames:
            jsc = self.getJobSummaryCount(errorName)
            if jsc.n > 0:
                jscNZ.append(jsc)
        return jscNZ

    def getHeaderCount(self):
        jsc = self.getJobSummaryCount('nRceSvtHeaders')
        return jsc.n

    def toString(self):
        s = 'Logfile run ' + str(self.run) + ':\n'
        for jsc in self.jobSummaryCounts:
            s += jsc.toString() + '\n'
        s += 'MultisampleErrors:'
        for mse in self.multisampleErrors:
            s += '\n' + mse.toString()
        return s + '\n'

def getRun(name):
    m = re.match('.*/?hps_00(\d*)\..*',name)
    if m != None:
        return int(m.group(1))
    else:
        print 'cannot get run number from ', name
        sys.exit(1)

def getFileId(name):
    m = re.match('.*/?hps_00(\d*)\.evio\.(\d+)\..*',name)
    if m != None:
        return int(m.group(2))
    else:
        print 'cannot get run number from ', name
        sys.exit(1)

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

