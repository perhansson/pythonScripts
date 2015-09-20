#!/usr/bin/python

import os,sys,argparse,subprocess,re
from ROOT import TFile, TH2, TGraph2D, TCanvas, gStyle

debug = False
rceHistNames = ['rceSyncError', 'rceOFError', 'rceSkipCount', 'rceMultisampleError']

def getNumbers(hist):
    m = {}
    for xbin in range(1, hist.GetXaxis().GetNbins()+1):
        bc = int(hist.GetXaxis().GetBinCenter(xbin))
        y1 = hist.GetBinContent(xbin,1)
        y2 = hist.GetBinContent(xbin,2)
        if debug: print 'xbin ', xbin, ' bc ', bc, ' y1 ', y1, ' y2 ', y2
        m[bc] =  [y2,y1]
    return m

class RceSummary(object):
    def __init__(self,run,roc,name):
        self.run = run
        self.roc = roc
        self.name = name
        self.n = 0
        self.e = 0

def printSummaries(summaries):
    for error in rceHistNames:
        print error
        nAll = 0
        eAll = 0
        runsAll = []
        for s in summaries:
            if s.name != error:
                continue
            nAll += s.n
            eAll += s.e
            if s.run not in runsAll:
                runsAll.append(s.run)
        
        print 'nAll: ', nAll, ' eAll', eAll, ' over ', len(runsAll), ' runs'
        #print 'run ' + str(self.run)
        #print '%5s %20s %20s %20s %20s' % ('ROC',rceHistNames[0],rceHistNames[1], rceHistNames[2], rceHistNames[3])
        #for roc in self.getRocIds():
        #    print '%5d %9d/%9d %9d/%9d %9d/%9d %9d/%9d' % (roc, self.counts[0][roc][0],self.counts[0][roc][1], self.counts[1][roc][0],self.counts[1][roc][1], self.counts[2][roc][0],self.counts[2][roc][1],self.counts[3][roc][0],self.counts[3][roc][1])

class RceResult(object):
    def __init__(self,run,histos):
        self.run = run
        self.histos = histos
        self.counts = []
        for hist in self.histos:
            self.counts.append(getNumbers(hist))

    def getRocIds(self):
        return self.counts[0].keys()

    def getHist(self,name):
        for h in self.histos:
            if h.GetName() == name:
                return h
        return None

    def printSummary(summaries):
        print 'run ' + str(self.run)
        print '%5s %20s %20s %20s %20s' % ('ROC',rceHistNames[0],rceHistNames[1], rceHistNames[2], rceHistNames[3])
        for roc in self.getRocIds():
            print '%5d %9d/%9d %9d/%9d %9d/%9d %9d/%9d' % (roc, self.counts[0][roc][0],self.counts[0][roc][1], self.counts[1][roc][0],self.counts[1][roc][1], self.counts[2][roc][0],self.counts[2][roc][1],self.counts[3][roc][0],self.counts[3][roc][1])
        


def getRun(name):
    m = re.search('.*hps_00(\d+)\.*',name)
    if m != None:
        if debug: print 'matched: ', int(m.group(1))
        return int(m.group(1)) 
    return -1


def getRceHists(tFile):
    histos = []
    for hName in rceHistNames:
        if debug: print 'getting ' + hName
        h = tFile.Get(hName)
        if h != None:
            histos.append(h)
        else:
            print 'couldnt get histo \"' + hName + '\"'
            sys.exit(1)
    return histos

def analyze(results):
    if debug: print 'analyze: ', len(results), ' results'
    runResults = {}
    listResults = []
    for r in results:
        #r.printSummary()
        if r.run not in runResults.keys():
            runResults[r.run] = []
            runResults[r.run].append( r )
        else:
            runResults[r.run].append( r )
        #for s in listResults:
            #if s.run
    if debug: print runResults

    errorGraphs2D = []
    totalGraphs2D = []
    errorsSum = {}
    
    for iError in range( len( rceHistNames ) ):
        if debug: print 'make error 2D graph for ', rceHistNames[iError]
        errorGraph = TGraph2D()
        totalGraph = TGraph2D()
        errorGraph.SetName('errorGraph_' + rceHistNames[iError])
        totalGraph.SetName('totalGraph_' + rceHistNames[iError])
        errorGraph.SetTitle('Error count ' + rceHistNames[iError])
        totalGraph.SetTitle('Total count ' + rceHistNames[iError])
        errorsSum[iError] = {}
        point = 0
        totErrors = 0
        for summary in results:
            if summary.name != rceHistNames:
                continue
            errorGraph.SetPoint(point,summary.run, summary.roc, summary.e)
            totalGraph.SetPoint(point,summary.run, summary.roc, summary.n)
            point = point + 1
        errorGraphs2D.append(errorGraph)
        totalGraphs2D.append(totalGraph)
    
    if debug: print errorGraphs2D
    if debug: print totalGraphs2D


    gStyle.SetPalette(1);
    cError = TCanvas('cErrorSummary','cErrorSummary',10,10,700,500)
    cError.Divide(2,2)
    cTotal = TCanvas('cTotalSummary','cTotalSummary',10,10,700,500)
    cTotal.Divide(2,2)
    for i in range( len( rceHistNames) ):
        if debug: print 'draw 2D graph ', rceHistNames[iError]
        cError.cd(i+1)
        errorGraphs2D[i].Draw('colz')
        cTotal.cd(i+1)
        totalGraphs2D[i].Draw('colz')
    cError.SaveAs(cError.GetName() + '.png')
    cTotal.SaveAs(cTotal.GetName() + '.png')
    ans = raw_input('continue?')
    



if __name__ == '__main__':
    print 'just go'

    parser = argparse.ArgumentParser()
    parser.add_argument('-f',required=True, nargs='+',help='Input ROOT files')
    parser.add_argument('-d', action='store_true',help='debug')
    args = parser.parse_args()
    print args

    debug = args.d
    tfiles = []
    rceResults = []
    
    for f in args.f:
        run = getRun(f)
        if run < 0:
            print 'Could not get run number from file ' + f
            sys.exit(1)
        
        tf = TFile(f)
        rceHists = getRceHists(tf)
        print 'Got ', len(rceHists), ' RCE histograms'
        rceResult = RceResult(run,rceHists)
        rceResults.append(rceResult)
        tfiles.append(tf)

    
    summaries = []
    for res in rceResults:
        for iError in range(len(rceHistNames)):
            for roc,val in res.counts[iError].iteritems():
                summary = None
                for s in summaries:
                    if res.run == s.run and roc == s.roc and s.name == rceHistNames[iError]:
                        summary = s
                if summary == None:
                    print 'didn\'t find summary for run ', res.run, ' roc ', roc
                    summary = RceSummary(res.run, roc, rceHistNames[iError])
                    summaries.append(summary)
                summary.e += val[0]
                summary.n += val[1]

    print 'Found ', len(summaries), ' summaries'
    #analyze(summaries)
    printSummaries(summaries)

    for tf in tfiles:
        tf.Close()

