#!/usr/bin/python
import os
import sys
import argparse
import re
import subprocess
import svtHeaderUtils

debug = False


def analyze():

    
    filenames = []
    if args.directory != None:
        for root, dirs, files in os.walk(args.directory, topdown=False):
            for name in files:
                filename = os.path.join(root, name)
                if args.r != None:
                    if re.match(args.r,os.path.basename(filename)) == None:
                        if args.debug: print 'no match ' , filename
                        continue
                filenames.append( filename )

    if args.inputfile != None:
        filenames.append( args.inputfile )

    print 'Got ', len(filenames), ' filenames'
    if args.test:
        for filename in filenames:
            print filename
    else:
        analyzeFiles(filenames)


def analyzeFiles(filenames):

    logs = []
    for filename in filenames:
        logs.append( analyzeLogFile(filename) )

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
    runs.sort()
    print '%5s %8s %11s %s' % ('run','Nevents','NbadEvents','filepaths')
    for run in runs:
        paths = ''
        for log in runlogs.getRunLog(run).logs: paths += log.filepath + ','
        print '%5d %8d %11d %s' % (run,runlogs.getNevents(run),runlogs.getNbad(run),paths)


    # process errors
    if not args.checkerrors:
        return
    
    for runlog in runlogs.runlogs:
        if args.debug: print 'analyze errors for run ', runlog.run
        runlog.errors = analyzeLogFileErrors(runlog)


    # types of errors
    types = [] 

    
    print 'Error statistics for ', len(runlogs.runlogs), ' run logs:'
    print '%5s %8s %11s %8s %20s %20s' % ('run','Nevents','NbadEvents','Nerrors','ROC w/ errors','Errortypes/counts')
    runs = runlogs.getRuns()
    for run in runs:

        # get summaries for this run
        summaries = runlogs.getErrors(run)

        # make sure they exist
        if summaries == None:
            print 'what?'
            sys.exit(1)

        # check stat
        ntoterrors = 0 # total errors
        rocs = [] # rocs with errors 
        str_types = '' # list of type of errors
        for s in summaries.errorsummaries:
            nerrors = 0 # errors for this type of error
            for rec,n in s.records.iteritems():
                if not rec.roc in rocs:
                    rocs.append(rec.roc)
                nerrors += n
            str_types += s.type + '/' + str(nerrors) + ','
            ntoterrors += nerrors
            if not s.type in types: types.append(s.type)
        
        # build list of rocs into a string
        str_rocs = ''
        for roc in rocs: str_rocs += str(roc) + ','

        # print table
        print '%5d %8d %11d %8d %20s %20s' % (run,runlogs.getNevents(run),runlogs.getNbad(run),ntoterrors,str_rocs,str_types)

    
    
    print 'Found total of ', len(types), ' errors among the runs'

    
    print 'Information on each error'
    for t in types:
        print '--> ', t, ' <--'
        runlist = []
        rocs = {}
        febs = {}
        n = 0
        for run in runs:
            
            summaries = runlogs.getErrors(run)

            if args.debug: print 'run ', run, ' has ', len(summaries), ' error summaries'

            for summary in summaries.errorsummaries:

                if args.debug: print 'check error summary ', summary.type

                # only process a specific error type
                if summary.type == t:
                    if args.debug: print 'process error summary ', summary.type, ' with ', len(summary.records), ' records'

                    # keep track of the runs that had this error
                    if not run in runlist: runlist.append(run)

                    # keep track of where the error happened
                    for rec in summary.records:
                        # count total occurance
                        n += 1
                        
                        # list of rocs/febs
                        if not rec.roc in rocs:  rocs[rec.roc] = []
                        if not rec.feb in rocs[rec.roc]: rocs[rec.roc].append(rec.feb)

                        # list of febs/hybrids
                        if not rec.feb in febs:  febs[rec.feb] = []
                        if not rec.hybrid in febs[rec.feb]: febs[rec.feb].append(rec.hybrid)
        
        print 'Total #     ', n
        print 'runs        ', runlist
        print 'rocs:febs   ', rocs
        print 'feb:hybrids ', febs


            

class ErrorRecord:
    def __init__(self,roc,feb,hybrid,apv):
        self.roc = roc
        self.feb = feb
        self.hybrid = hybrid
        self.apv = apv

    def __hash__(self):
        return 0

    def __eq__(self, other):
        if self.roc == other.roc and self.feb == other.feb and self.hybrid == other.hybrid and self.apv == other.apv:
            return True
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)



class ErrorSummary:
    def __init__(self,t):
        self.type = t
        self.records = {}

    def addRecord(self,roc,feb,hybrid,apv):
        r = ErrorRecord(roc,feb,hybrid,apv)
        self.add(r)
    
    def hasRecord(self, record):
        for r in self.records.keys():
            if r == record:
                return True
        return False
    
    def add(self,record):
        if not self.hasRecord(record):
            self.records[record] = 0
        else:
            self.records[record] += 1

            
class ErrorSummaries:
    def __init__(self):
        self.errorsummaries = []
    def has(self,errortype):
        for es in self.errorsummaries:
            if es.type == errortype:
                return es
        return None
    def add(self,errsum):
        if self.has(errsum.type):
            print 'ERROR: trying to add summary that already exists'
            sys.exit(1)
        self.errorsummaries.append(errsum)
        

            
    
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

    summaries = ErrorSummaries()

    # exist if no bad events are found
    nbad = 0
    for log in runlog.logs:
        nbad += log.Nbad
    if nbad== 0:
        if args.debug: print ' no errors found'
        return summaries

    if args.debug: print ' found ', nbad, ' errors'

    # loop over all runs and build summaries
    for log in runlog.logs:
        count = 0
        print 'build summary for log file in run ', runlog.run
        filename = log.filepath

        with open(filename,'r') as f:
            for lineraw in f:
                if count%10000==0: print 'processed ', count, 'lines'
                count+=1
                # match this line
                line = lineraw.rstrip()
                #SvtHeaderAnalysisDriver INFO: Run 5579 event 41403468 Exception type SvtEvioHeaderApvFrameCountException for roc 57 feb 4 hybrid
                m = re.match('SvtHeaderAnalysisDriver\s.*Run\s(\d+)\sevent\s(\d+)\sException type\s(\S+)\s.*roc\s(\d+)\sfeb\s(\d+)\shybrid\s(\d+)\sapv\s(\d+).*',line)
                if m != None:

                    if args.debug: print ' matched line \"', line,'\"'
                    
                    run = int(m.group(1))
                    event = int(m.group(2))
                    errortype = m.group(3)
                    roc = int(m.group(4))
                    feb = int(m.group(5))
                    hybrid = int(m.group(6))
                    apv = int(m.group(7))
                    #error = DaqError(run,event,errortype,roc,feb,hybrid,apv)

                    #find the summary for this type
                    summary = summaries.has(errortype)
                    if summary == None:
                        # not there, create it
                        if args.debug: print ' create new summary for type ', errortype
                        summary = ErrorSummary(errortype)
                        # add it to the list of summaries
                        summaries.add( summary ) 
                    
                    # got the summary, add the record to it
                    if args.debug: print ' add new record for type ', errortype
                    summary.addRecord(roc,feb,hybrid,apv)
                    if args.debug: print len(summary.records) , ' records in the summary right now'
    
    #if args.debug:
    #print 'found ', len(errors), ' errors from run ', runlog.run
    print 'found ', len(summaries.errorsummaries), ' error summaries built from run ', runlog.run
    return summaries



if __name__ == '__main__':
    print 'just go'


    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--directory', help='Directory to scan for log files')
    parser.add_argument('-i','--inputfile', help='Input file')
    parser.add_argument('-r',required=False ,help='regexp in log file name')
    parser.add_argument('--debug', action='store_true',help='debug')
    parser.add_argument('--test', action='store_true',help='only test')
    parser.add_argument('--checkerrors','-c', action='store_true',help='do error analysis')
    parser.add_argument('-n', type=int, default=-1, help='restrict nr')
    args = parser.parse_args()
    print args
    
    debug = args.debug

    analyze()




