#!/usr/bin/python

import sys,argparse,re, os.path
from ROOT import TH2F, TH1F, TCanvas

debug = False


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


def analyze(filepath):
    print 'analyze ', filepath
    run = getRun(os.path.split(filepath)[1])
    if debug: print 'run ', run
    f  = open(filepath,'r')
    log = LogFile(run)
    for l in f.readlines():
        if debug or 'tail' in l: print 'analyze line \"', l, '\"'

        m = MultiSampleError.matchLine(l)
        if m != None:
            mse = MultiSampleError( int(m.group(1)), int(m.group(2)), m.group(3), int(m.group(4)), int(m.group(5)), int(m.group(6)), int(m.group(7)) )
            if debug: print mse.toString()
            log.multisampleErrors.append(mse)
            if 'tail' in l: print 'found MSE in line ', l
        else:
            if 'tail' in l: print 'NO MSE in line ', l

        m = SyncError.matchLine(l)
        if m != None:
            se = SyncError( int(m.group(1)), int(m.group(2)), int(m.group(4)), m.group(3) )
            if debug: print se.toString()
            log.syncErrors.append(se)

        m = JobSummaryCount.matchLine(l)
        if m != None:
            jsc = JobSummaryCount(run,m[0], int(m[1].group(1)))
            log.jobSummaryCounts.append( jsc )
        
    f.close()
    return log



def printSummary(runLogs):
    if debug:
        print 'printSummary for '
        print runLogs

    nHeaders = 0
    nErrors = 0
    multisampleErrors = []
    syncErrors = []
    allErrors = []
    nErrorsType = {}
    for name in JobSummaryCount.errorNames: nErrorsType[name] = 0
    for run in sorted(runLogs):
        if debug: print 'run ', run
        nErrorsRun = 0
        nHeadersRun = 0
        multisampleErrorsRun = []
        syncErrorsRun = []
        nErrorsTypeRun = {}
        for name in JobSummaryCount.errorNames: nErrorsTypeRun[name] = 0
        logsForRun = runLogs[run]
        for log in logsForRun:
            if debug: print 'looking at ', log.toString()
            nHeadersRun += log.getHeaderCount()
            multisampleErrorsRun.extend( log.multisampleErrors )
            syncErrorsRun.extend( log.syncErrors )
            for errorName in JobSummaryCount.errorNames:
                jsc = log.getJobSummaryCount(errorName)
                if jsc.n > 0:
                    allErrors.append(jsc)
                    if errorName not in nErrorsType:
                        print 'error, what?'
                        sys.exit(1)
                    nErrorsTypeRun[errorName] += jsc.n
                    nErrorsRun += jsc.n
            if debug:
                print 'nErrorsRun ', nErrorsRun
                print 'nHeadersRun ', nHeadersRun
                print 'nMultisampleErrorsRun ', len(multisampleErrorsRun)
                print 'nSyncErrorsRun ', len(syncErrorsRun)
                print 'nErrorsTypeRun ', nErrorsTypeRun
        nErrors += nErrorsRun
        nHeaders += nHeadersRun
        multisampleErrors.extend( multisampleErrorsRun )
        syncErrors.extend( syncErrorsRun )
        for name,count in nErrorsTypeRun.iteritems():
            nErrorsType[name] += count
        if debug:
            print 'Total so far'
            print 'nMultisampleErrors ', len(multisampleErrors)
            print 'nSyncErrors ', len(syncErrors)
            print 'nErrors ', nErrors
            print 'nErrorsType ', nErrorsType
            
    print '==='
    print 'Total nr of runs: ', len(runLogs)
    print 'Total SVT headers analyzed:       ', nHeaders, '( 14 ROCs/event =>  ~',nHeaders/14 ,' events)'
    print 'Total SVT header errors: ', nErrors, ' (fraction of headers with error ', float(nErrors)/nHeaders, ')'
    for name,count in nErrorsType.iteritems():
        print 'Total SVT headers with ', name,' errors: ', count ,  ' (fraction of headers with error ', float(count)/nHeaders, ')'

    hMSE_feb_hyb_id = TH2F('hMSE_feb_hyb_id','FEB and Hybrid Id MSE;Feb Id;Hybrid Id',11, -0.5, 10.5, 5, -0.5, 4.5)
    hSE_roc_id = TH1F('hSE_roc_id','ROC Id SE;Errors;ROC Id',21, 49.5, 70.5)
    hMSE_hyb_apv_id = {}

    print 'SyncErrors logged: ', len(syncErrors) , ' (fraction of headers with error ', float(len(syncErrors))/nHeaders, ')'
    for e in syncErrors:
        hSE_roc_id.Fill( e.roc )
    
    print 'Total multisampleheader errorbits: ', len(multisampleErrors) , ' (fraction of headers with error ', float(len(multisampleErrors))/nHeaders, ')'
    print '==='
    print 'List of all multisample errorbits:'
    print '%5s %10s %10s %10s %10s %10s ' % ('run','event','rce/roc','feb','hybrid','apv')
    for e in multisampleErrors:
        print '%5d %10d %10d %10d %10d %10d ' % (e.run,e.event,e.roc,e.feb,e.hybrid,e.apv)
        hMSE_feb_hyb_id.Fill(e.feb,e.hybrid)
        if not e.feb in hMSE_hyb_apv_id:
            hMSE_hyb_apv_id[e.feb] = TH2F('hMSE_feb'+str(e.feb)+'_hyb_apv_id','FEB ' + str(e.feb) + ' Hybrid and APV Id MSE;Hybrid Id;APV Id',5, -0.5, 4.5, 6, -0.5, 5.5)
        hMSE_hyb_apv_id[e.feb].Fill(e.hybrid,e.apv)
            
    print '==='
    for name in JobSummaryCount.errorNames:
        print 'List of runs with SVT header error \"',name,'\"'
        mydict = {}
        for jsc in allErrors:
            if jsc.name == name:
                if jsc.run not in mydict:
                    mydict[jsc.run] = 0
                mydict[jsc.run] += jsc.n
        print '%5s %s' % ('run','#headers w/ error')
        for run,count in mydict.iteritems():
            print '%5d %d' % (run,count)

    c_se_roc = TCanvas('c_se_roc','c_se_roc',10,10,700,500)
    hSE_roc_id.Draw()
    c_mse_feb = TCanvas('c_mse_feb','c_mse_feb',10,10,700,500)
    hMSE_feb_hyb_id.SetMarkerSize(2.0)
    hMSE_feb_hyb_id.Draw('colz,text')
    c_mse_hyb = []
    for feb,h in hMSE_hyb_apv_id.iteritems():
        c = TCanvas('c_hyb_feb_' + str(feb),'c_hyb_feb_' + str(feb),10,10,700,500)
        h.SetMarkerSize(2.0)
        h.Draw('colz,text')
        c.SaveAs(c.GetName() + '.png','png')
        c_mse_hyb.append(c)
    #ans = raw_input('cont?')
    



if __name__ == '__main__':
    print 'just go'

    parser = argparse.ArgumentParser()
    parser.add_argument('-f',required=True ,help='Input log files')
    parser.add_argument('-r',required=False ,help='regexp in log file name')
    parser.add_argument('-d', action='store_true',help='debug')
    parser.add_argument('-n', type=int, default=-1, help='restrict nr')
    args = parser.parse_args()
    print args
    
    debug = args.d
    
    print 'Mining ', args.f, ' directory'
    
    logs = []
    for root, dirs, files in os.walk(args.f):
        if args.n > 0 and len(logs) > args.n:
            break
        if debug: print 'len of dirs ', len(dirs)
        for d in dirs:
            if debug: print 'check dir ', d
            #if not 'linkerror' in d:
            #    if debug: print ' remove ', d
            #    dirs.remove(d)
        
        if debug: print 'len of dirs after ', len(dirs)
        for name in dirs:
            if debug: print 'mine dir ', name
                
        for n in files:
            # check reg exp
            if args.r != None:
                if re.match(args.r,n) == None:
                    continue
            b, e = os.path.splitext(n)
            if e != '.log':
                continue
            fpath = os.path.join(root,n)
            if debug:
                print 'mine name ', n, ' size ', os.path.getsize(fpath)
            if os.path.getsize(fpath) == 0:
                print 'skipping zero size ', fpath
                continue
            l = analyze( fpath )
            if debug: print 'Analyzed ' , l.toString()
            logs.append( l )
    
    print 'Found ', len(logs), ' logs'
    runLogs = {}
    for log in logs:
        if log.run not in runLogs:
            runLogs[log.run] = []
        runLogs[log.run].append(log)

    printSummary(runLogs)




