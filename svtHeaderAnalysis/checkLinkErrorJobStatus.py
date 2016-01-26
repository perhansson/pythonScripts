import os, re, subprocess, argparse, sys
from utils import Logs, Log, LockedLog, HeaderException, getLogs, getEvioFileList, getRunDict, processEventTimeFile
from constants import IGNORE_RUNS


parser = argparse.ArgumentParser()
parser.add_argument('--logdir', nargs='+', required=True, help='Directories of log files')
parser.add_argument('--eviodir', help='Check and use EVIO files')
parser.add_argument('--eventtimefile', help='Check that a supplied event time exists for each locked run')
parser.add_argument('--debug','-d', action='store_true', help='debug flag')
args = parser.parse_args()
print args


# directory where I keep the locked runs evio files
evioDirLockedFiles = '/nfs/slac/g/hps3/users/phansson/data/engrun/evio/SvtLockedRunFiles'
#get a list of all the files
lockedEvioFiles = os.listdir(evioDirLockedFiles)


print 'EVIO file directory: ', args.eviodir
print 'Log  file directory: ', args.logdir

filelist = []
logsRaw = Logs()

if args.eviodir != None:
    print 'Find logs via evio files in \"', args.eviodir,'\"'
    if len(args.logdir) != 1:
        raise HeaderException('not implemented yet? Not sure if it works')
    filelist = getEvioFileList(args.eviodir)
    logsRaw.addList(getLogs(args.eviodir,args.logdir[0]),False)
else:
    for logdir in args.logdir:
        logsRaw.addList( getLogs(None,logdir), False )

    

print 'Found ', len(filelist), ' evio files:'
print 'Found ', len(logsRaw.logs), ' raw logs'
print 'Process files'
for log in logsRaw.logs:
#    print 'process log ', log.filenr, ' from run ', log.run
    log.processTail()
print 'Done'

logs = Logs()
logs.addList(logsRaw.logs, True)

print 'Found ', len(logs.logs), ' logs after duplicates removed'

#print 'logs:'
#for log in logs.logs:
#    print 'log ', log.filenr, ' from run ', log.run

# sort according to run
logs.logs.sort(key=lambda x:x.run)

#print 'sorted logs:'
#for log in logs.logs:
#    print 'log ', log.filenr, ' from run ', log.run

# characeterize the logs into different classes
logsAll = []
logsWithResult = []
logsLocked = []
logsNoLockError = []
logsWithAnyError = []
logsLockedActive = []
logsGood = []

print '%5s %5s %10s %10s %15s %15s %s' % ('run','logNr','Nevents','Nbadevents','eviofilesize','logfilesize','logfile')
for log in logs.logs:

    if log.eviofile == None: evioS = 'None'
    else: evioS = str(os.path.getsize(log.eviofile))
    
    if log.logfile == None:
        logS = 'None'
        logF = '-'
    else:
        logS = str(os.path.getsize(log.logfile))
        logF = log.logfile

    logsAll.append(log)

    # pick out logs and count
    # only do it for those that had some events
    if log.nevents > 0:

        # list of logs with clear results on accounting of errors in the file
        logsWithResult.append(log)

        # list all that are ok
        if log.nbadevents == 0:
            logsGood.append(log)
            
        # categorize those that had errors
        else:
            
            # this log had some event with error
            logsWithAnyError.append(log)
            
            # Loop through the errors and categorize them
            readErr = False
            msErr = False
            syncErr = False
            frameCountErr = False
            msErrSummary = None
            for error in log.errors:
                if 'SvtEvioHeaderSyncErrorException' in error.name:
                    syncErr = True
                if 'SvtEvioHeaderApvFrameCountException' in error.name:
                    frameCountErr = True
                if 'SvtEvioHeaderApvReadErrorException' in error.name:
                    readErr = True
                if 'SvtEvioHeaderMultisampleErrorBitException' in error.name:
                    msErr = True
                    msErrSummary = error

            # 1. If there is a SvtHeaderSyncError it locked
            if syncErr:
                log.locked.append(1)

            # check other errors, gets a little messy here...
            else:
                # 2. Without syncerror,
                #    If there was no MS error then there might have been a lockup
                if not msErr:
                    if readErr or frameCountErr:
                        print 'Run ', log.run, ' logfilenr ', log.filenr, ': no MS error but readErr or frameCountErr -> locked'
                        log.locked.append(2)
                # 3. If there was a MS error, check if it was responsible for all the other errors
                else:
                    for error in log.errors:
                        # skip if it's the MS error
                        if error.name == msErrSummary.name:
                            continue
                        # check ROCs
                        for roc,count in error.rocs.iteritems():
                            # if the error is not on the same roc as the MS there should be a lock
                            if roc not in msErrSummary.rocs.keys():
                                print 'Run ', log.run, ' logfilenr ', log.filenr, ': An ', error.name, ' on roc ', roc, ' is not among the ',len(msErrSummary.rocs), '(',msErrSummary.rocs.keys(),') with MS error'
                                log.locked.append(3)
                            # check that thec counts were the same on the ROCs
                            else:
                                # up to 6 frame count errors per MS error
                                if 'SvtEvioHeaderApvFrameCountException' in error.name:
                                    if count > (msErrSummary.rocs[roc] * 6) :
                                        print 'Run ', log.run, ' logfilenr ', log.filenr, ': The ', error.name, ' on roc ', roc, ' has different counts ', count,' than the MS error on that roc ', msErrSummary.rocs[roc], ' -> locked'
                                        log.locked.append(4)                                    
                                # otherwise make sure it's the same count 
                                elif 'SvtEvioHeaderApvReadErrorException' in error.name:
                                    if count < msErrSummary.rocs[roc] or count > (msErrSummary.rocs[roc] * 6) :
                                        print 'Run ', log.run, ' logfilenr ', log.filenr, ': The ', error.name, ' on roc ', roc, ' has different counts ', count,' than the MS error on that roc ', msErrSummary.rocs[roc], ' -> locked'
                                        log.locked.append(5)                                    
                                # otherwise make sure it's the same count
                                else:
                                    if count != msErrSummary.rocs[roc]:
                                        print 'Run ', log.run, ' logfilenr ', log.filenr, ': The ', error.name, ' on roc ', roc, ' has different counts ', count,' than the MS error on that roc ', msErrSummary.rocs[roc], ' -> locked'
                                        log.locked.append(6)
            

            
            # 3. Clearly, if every single event had an error it locked, check consistency
            if log.nevents == log.nbadevents:
                if not log.isLocked():
                    raise HeaderException('This log had error on every event but is not characterized as locked?\n ' + log.__str__())


            # list of logs that had a lock
            if log.isLocked():
                logsLocked.append(log)

                # list of logs where the lock event happened during this particular log file
                lockedDuringRun = False

                # If there are not errors on all events it happeneded here
                if log.nevents > log.nbadevents:
                    lockedDuringRun = True
                # with the exception if it's the first file (by construction)
                if log.nevents == log.nbadevents and log.filenr == 0:
                    lockedDuringRun = True

                # add them to list
                if lockedDuringRun:
                    logsLockedActive.append(LockedLog(log))
            
            # list of logs that had a non-locking error
            else:
                logsNoLockError.append(log)
    

    
    
    print '%5d %5d %10d %10d %15s %15s %s' % (log.run,log.filenr,log.nevents,log.nbadevents,evioS,logS,logF)




print '\n\n--> Log Summary <--'
print 'Run logs                                 : ', len(logsAll)
print 'Run logs w/ results                      : ', len(logsWithResult)
print 'Run logs w/o any errors                  : ', len(logsGood)
print 'Run logs w/  any errors                  : ', len(logsWithAnyError)
print 'Run logs w/ errors on fraction of events : ', len(logsNoLockError)
print 'Run logs w/ identified lockup            : ', len(logsLocked)
print 'Run logs w/ active lockup                : ', len(logsLockedActive)


# collect the logs in a dict with the run numbers as key
runsAll = getRunDict(logsAll)
runsWithResult = getRunDict(logsWithResult)
runsWithAnyError = getRunDict(logsWithAnyError)
runsGood2 = getRunDict(logsGood)
runsNoLockError2 = getRunDict(logsNoLockError)
runsLocked = getRunDict(logsLocked)
runsLockedActive = getRunDict(logsLockedActive)
runsWithoutResult = {}
runsWithoutResultCare = {}
# find the runs with no results
for r,l in runsAll.iteritems():
    if r not in runsWithResult:
        runsWithoutResult[r] = l
        if r not in IGNORE_RUNS:
            runsWithoutResultCare[r] = l
            

# take care of overlaps
runsGood = {}
for r,l in runsGood2.iteritems():
    if r not in runsWithAnyError:
        runsGood[r] = l
runsNoLockError = {}
for r,l in runsNoLockError2.iteritems():
    if r not in runsLocked:
        runsNoLockError[r] = l
for r,llogs in runsLockedActive.iteritems():
    if len(llogs) > 1:
        selLockLog = None
        for llog in llogs:
            if selLockLog == None:
                selLockLog = llog
            else:
                if llog.log.filenr < selLockLog.log.filenr:
                    selLockLog = llog
        runsLockedActive[r] = [selLockLog]



print '\n\n--> Run Summary <--'
print 'Runs (all)                           : ', len(runsAll)
print 'Runs without results                 : ', len(runsWithoutResult)
print 'Runs without results we care about   : ', len(runsWithoutResultCare)
print 'Runs with results                    : ', len(runsWithResult)
print 'Runs without any errors              : ', len(runsGood)
print 'Runs with any error                  : ', len(runsWithAnyError)
print 'Runs not locked but with errors      : ', len(runsNoLockError)
print 'Runs locked                          : ', len(runsLocked)
print 'Runs with active lockup              : ', len(runsLockedActive)

# sort keys for later
runsLocked_keys = runsLocked.keys()
runsLocked_keys.sort()



print '\n--> More details on each category <--'

print '\nNo result for runs:'
for r in runsWithoutResult.keys():
    print r

print '\nNo result for runs that we care about:'
for r in runsWithoutResultCare.keys():
    print r




print '\nRun logs w/ no error: ', len(logsGood)
print '%5s %10s' % ('run','nEvents')
countsTot = [0,0]
for log in logsGood:
    counts = [log.nevents, log.nbadevents]
    print '%5d %10d ' % (log.run,counts[0])
    countsTot[0] += counts[0]
    countsTot[1] += counts[1]
print '%5s %10d ' % ('Total',countsTot[0])


print '\nRun logs not locked but with errors: ', len(logsNoLockError)
print '%5s %5s %10s %10s %10s %10s' % ('run', 'logNr','nEvents','nBadEvents','fractionBad','Errors')
countsTot = [0,0]
for log in logsNoLockError:
    counts = [log.nevents, log.nbadevents]
    frac = -1.0
    if counts[0] != 0: frac = float(counts[1])/counts[0]
    error_names = ''
    for error in log.errors: error_names += error.name + ','
    print '%5d %5d %10d %10d %10f %10s' % (log.run,log.filenr,counts[0],counts[1],frac,error_names)
    countsTot[0] += counts[0]
    countsTot[1] += counts[1]
fracTot = -1.0
if countsTot[0] != 0: fracTot = float(countsTot[1])/countsTot[0]
print '%5s %10d %10d %10f' % ('Total',countsTot[0],countsTot[1],fracTot)



print '\n\nRun logs that were locked: ', len(logsLocked)
print '%5s %5s %7s %10s %10s %10s %30s' % ('run','logNr','lockIDs','nEvents','nBadEvents','evioFileId','ErrorName/roc:count')
for log in logsLocked:
    # find evio file nr for this case
    i = -1
    m = re.match('.*hps_00\d+\.evio\.(\d+).*',os.path.basename(log.logfile))
    if m != None: i = int( m.group(1) ) 
    error_names = ''
    for error in log.errors:
        error_names += error.name + '/' + str(error.rocs) + ','
    lockedids = ','
    lockedids = lockedids.join( log.locked_str() )
    print '%5d %5d %7s %10d %10d %10d %30s' % (log.run,log.filenr,lockedids,log.nevents,log.nbadevents,i,error_names)


print '\n\nRun logs that were locked but not on all events: ', len(logsLocked)
print '%5s %5s %7s %10s %10s %10s %30s' % ('run','logNr','lockIDs','nEvents','nBadEvents','evioFileId','ErrorName/roc:count')
for log in logsLocked:
    if log.nevents == log.nbadevents:
        continue
    # find evio file nr for this case
    i = -1
    m = re.match('.*hps_00\d+\.evio\.(\d+).*',os.path.basename(log.logfile))
    if m != None: i = int( m.group(1) ) 
    error_names = ''
    for error in log.errors:
        error_names += error.name + '/' + str(error.rocs) + ','
    lockedids = ','
    lockedids = lockedids.join( log.locked_str() )
    print '%5d %5d %7s %10d %10d %10d %30s' % (log.run,log.filenr,lockedids,log.nevents,log.nbadevents,i,error_names)


print '\n\nRun logs w/ lock happening during a log that I processed: ', len(logsLockedActive)
print '%5s %5s %7s %10s %10s %10s %10s %35s %10s' % ('run','logNr','lockIDs','nEvents','nBadEvents','fractionBad','Err@Event','Err@Date','Errors')
countsTot = [0,0]
for lockedlog in logsLockedActive:
    log = lockedlog.log
    counts = [log.nevents, log.nbadevents]
    frac = -1.0
    if counts[0] != 0: frac = float(counts[1])/counts[0]
    error_names = ''
    for error in log.errors: error_names += error.name + ','
    lockedids = ','
    lockedids = lockedids.join( log.locked_str() )
    print '%5d %5d %7s %10d %10d %10f %10d %35s %10s' % (log.run,log.filenr,lockedids,counts[0],counts[1],frac,lockedlog.lock.event, lockedlog.lock.dateStr, error_names)
    countsTot[0] += counts[0]
    countsTot[1] += counts[1]
fracTot = -1.0
if countsTot[0] != 0: fracTot = float(countsTot[1])/countsTot[0]
print '%5s %5s %7s %10d %10d %10f %10s %35s %10s' % ('Total','','',countsTot[0],countsTot[1],fracTot,'','','')




print '\n\nInformation on all runs analyzed that we care about'
print '%5s %s' % ('run','Information')
for r in runsAll.keys():

    if r in IGNORE_RUNS:
        continue
    
    s = ''
    if r not in runsWithResult:
        s += 'NO INFO'
    else:
        if r in runsGood:
            s += 'OK'
        else:
            if r in runsLocked:
                s += 'LOCKED '
                if r in runsLockedActive:
                    s += 'AT KNOWN EVENT '
                else:
                    s += 'UNKOWN WHEN '
            elif r in runsNoLockError:
                s += 'DAQ ERROR'
            else:
                raise HeaderException('should never get here for run ', r)
    print '%5d %s' % (r,s)



lockedRunEventTimeMap = None
if args.eventtimefile != None:
    lockedRunEventTimeMap = processEventTimeFile(  args.eventtimefile )

filesActiveLockLogFiles = []
lockedRunEventMap = {}


print '\nInformation on lock position for each of the locked runs that we care about'
print '%5s %5s %10s %22s %35s' % ('run','logNr','Err@Event','Err@EventTime','Err@Date')
for r in runsLocked_keys:
    
    if r in IGNORE_RUNS:
        continue

    lockedlog = None
    if r not in runsLockedActive:
        # find the earliest log I have
        selLog = None
        for log in runsLocked[r]:
            if selLog == None:
                selLog = log
            else:
                if log.filenr < selLog.filenr:
                    selLog = log
        print '%5d %5d %10s %22s %35s' % (r,selLog.filenr,'?','?','Earliest log on disk')
    else:
        lockedlogs = runsLockedActive[r]
        if len(lockedlogs) != 1:
            print 'there are ', len(lockedlogs), ' locked logs for run ', r, ' !?'
        for llog in lockedlogs:
            # check separate event time file, if supplied
            if args.eventtimefile != None:
                #print len(lockedRunEventTimeMap), ' runs to check'
                time = -1
                if llog.run in lockedRunEventTimeMap:
                    if lockedRunEventTimeMap[llog.run][0] == llog.lock.event:
                        time = lockedRunEventTimeMap[llog.run][1]
                    else:
                        print 'Event is not the same!?'
            print '%5d %5d %10d %22d %35s' % (llog.log.run,llog.log.filenr,llog.lock.event, time, llog.lock.dateStr)
            filesActiveLockLogFiles.append(llog.log.logfile)
            lockedRunEventMap[llog.log.run] = llog.lock.event
            



fLL = open('locked_files.txt','w')
for lf in filesActiveLockLogFiles:
    fname = os.path.basename(lf).split('.log.1')[0]
    fLL.write(fname + '\n')
fLL.close()
fLL = open('locked_run_event_map.txt','w')
for run_lf, evt_lf in lockedRunEventMap.iteritems():
    fLL.write(str(run_lf) + ' '  + str(evt_lf) + '\n')
fLL.close()



    






print '\nFind range of files to download for locked runs that we care about'
print 'Go through each locked log file and find the previous one that was ok, if any'
logsLockedToPrev = {}
logsLockedAllPrev = {}
logsLockedAllPrevRes = {}
print '%5s %20s %20s' % ('Run','File locked','Prev. OK file')

for r in runsLocked_keys:

    if r in IGNORE_RUNS:
        continue
    
    if r not in runsLockedActive:
        # find the earliest locked log
        selLog = None
        for log in runsLocked[r]:
            if selLog == None:
                selLog = log
            else:
                if log.filenr < selLog.filenr:
                    selLog = log
        
        #find the previous log with results that was NOT locked
        prevLog = None
        for log in runsWithResult[r]:
            if log == selLog:
                continue
            if log.filenr < selLog.filenr:
                if prevLog == None:
                    prevLog = log
                else:
                    if log.filenr > prevLog.filenr:
                        prevLog = log

        # these have no prev log with results
        if prevLog == None:
            # print the logs with result and all the logs as debug)
            s = 'No prev log ('
            s += str(len(runsWithResult[r])) + ' logs w/ result: '
            for l in runsWithResult[r]: s += str(l.filenr) + ','
            s += ' and ' + str(int(len(runsAll[r]))) + ' nr of logs: '
            for l in runsAll[r]: s += str(l.filenr) + ','
            s += ')'
            print '%5d %20d %20s' % (selLog.run,selLog.filenr,s)
            # save to a list all prev logs w/ or w/o results 
            for l in runsAll[r]:
                if l.filenr < selLog.filenr:
                    if r not in logsLockedAllPrev: logsLockedAllPrev[r] = []
                    logsLockedAllPrev[r].append(l)
        else:
            print '%5d %20d %20d' % (selLog.run,selLog.filenr,prevLog.filenr)
            # save to a list all prev logs between the locked and the OK one
            for l in runsAll[r]:
                if l.filenr < selLog.filenr and l.filenr > prevLog.filenr:
                    if r not in logsLockedAllPrevRes: logsLockedAllPrevRes[r] = []
                    logsLockedAllPrevRes[r].append(l)
            
        logsLockedToPrev[r] = [selLog,prevLog]



# sort according to run



#print '\n\nBelow are the earlier logs for locked runs that had no prev unlocked log found'
#logsLockedAllPrev_keys = logsLockedAllPrev.keys()
#logsLockedAllPrev_keys.sort()
#for r in logsLockedAllPrev_keys:
#    vlogs = logsLockedAllPrev[r]
#    print 'Run ', r, ' has ', len(vlogs), ' logs'
#    for l in vlogs:
#        print l



print '\n\nBelow is the range of files that I need to process to find the locked position'
print 'If the start file is -1 it means there was no prev log with result'
jcachelist = []
disklist = []
logsLockedToPrev_keys = logsLockedToPrev.keys()
logsLockedToPrev_keys.sort()
for r in logsLockedToPrev_keys:
    v = logsLockedToPrev[r]
    llog = v[0]
    plog = v[1]
    m = re.match('.*hps_00(\d+)\.evio\.(\d+).*',llog.logfile)
    if m == None:
        raise HeaderException('what?')
    run = int(m.group(1))
    if r != run:
        raise HeaderException('whatta')
    ilock = int(m.group(2))
    istart = -1
    if plog != None:
        m = re.match('.*hps_00(\d+)\.evio\.(\d+).*',plog.logfile)
        if m == None:
            raise HeaderException('what?')
        run = int(m.group(1))
        if r != run:
            raise HeaderException('whatta')
        istart = int(m.group(2)) + 1 
    print 'Run ', r, ' range [',istart,',',ilock-1,']'

    # print list of evio files, either on disk or cache
    if istart == -1: istart = 0
    for i in range(istart,ilock):
        # look if they are on disk already
        fname = 'hps_00%d.evio.%d' % (r,i)
        if fname in lockedEvioFiles:
            # found it on disk
            fname = os.path.join(evioDirLockedFiles,fname)
            print fname
            disklist.append(fname)
        else:
            # not on disk, need to stage 
            p = '/mss/hallb/hps/data/'
            print os.path.join(p,fname)
            jcachelist.append(os.path.join(p,fname))


# print help for submitting new jobs on batch
print '\n\nThere are in total ', len(disklist), ' evio files that seem to be on disk already'
for f in disklist:
    print f

# print help for caching new files
jcacheliststr = ' '
jcacheliststr = jcacheliststr.join(jcachelist)
print '\n\nThere are in total ', len(jcachelist), ' files to get from cache'
if 1==1:
    print 'jcache command for ', len(jcachelist), ' files:'
    print 'jcache submit default ', jcacheliststr




print '\nNew files to download for runs we care about and had no info'
runlist = []
for r in runsWithoutResultCare.keys():
    print 'Run ', r
    print 'Find existing files on disk'
    #print 'look for earlier log file for run ', selLog.run, ' filenr ', selLog.filenr
    files = []
    for fname in os.listdir(evioFileDir):
        m = re.match('.*hps_00(\d+)\.evio\.(\d+)',fname)
        if m != None:
            run = int(m.group(1))
            i = int(m.group(2))
            if run == r:
                files.append(fname)
    print 'Found ', len(files), ':'
    for f in files:
        print f
    # add to list
    runlist.append(r)
print 'Clean list to re-run on batch farm'
for r in runlist:
    print r


    

                        


