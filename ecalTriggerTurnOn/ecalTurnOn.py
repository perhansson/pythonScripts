#!/usr/bin/python

import os,sys,argparse,subprocess,re
from ROOT import TFile, TH2F, TGraph2D, TCanvas, gStyle,TGraphAsymmErrors
sys.path.append('../')
import plotutils


debug = False
tFiles = []


def getEffGr(hNum, hDen):
    gr = TGraphAsymmErrors()
    gr.BayesDivide(hNum, hDen)
    #gr.Divide(hNum, hDen, 'cl=0.683 b(1,1) mode')
    return gr


def getHistogram(name):
    hsum = None
    for tfile in tFiles:
        h = tfile.Get(name)
        print f,': h ', h.GetName(), ' entries ', h.GetEntries()
        if hsum == None:
            hsum = h
        else:
            hsum.Add(h)
        print 'hsum ', hsum.GetEntries()
    return hsum


def getTriggerEfficiency(num, den, name = ''):
    
    hNum = getHistogram(num)
    hDen = getHistogram(den)

    # get efficiency
    gr = getEffGr(hNum, hDen)
    gr.SetTitle(num + ';Cluster energy (GeV);Trigger efficiency')

    # plot
    c = TCanvas('c','c',10,10,700,1000)
    c.Divide(1,3)
    c.cd(1)
    hNum.Draw()
    c.cd(2)
    hDen.Draw()

    c.cd(3)
    plotutils.setGraphStyle(gr)
    gr.Draw('AP')

    c.SaveAs('trigeff-input-' + num + name + '.png')

    #ans = raw_input('cont?')

    return gr





if __name__ == '__main__':
    print 'just go'

    parser = argparse.ArgumentParser()
    parser.add_argument('-f',required=True, nargs='+',help='Input ROOT files')
    parser.add_argument('-d', action='store_true',help='debug')
    args = parser.parse_args()
    print args

    debug = args.d

    for f in args.f:
        tfile = TFile(f)
        tFiles.append(tfile)

    #  histogram names
    num = 'clusterEOne_RandomSingles1'
    den = 'clusterEOne_Random'

    getTriggerEfficiency(num, den, '-all')

    grs = {}
    cName = 'c_overlay'
    c22 = TCanvas(cName,cName,10,10,1000,1000)
    c22.Divide(1,2)
    h22 = TH2F('h22',';Offline cluster energy (GeV);Trigger efficiency',10,0,1.4,10,0,1.1)
    h22.SetStats(False)
    c22.cd(1)
    h22.Draw()
    c22.cd(2)
    h22.Draw()

    grs = {}
    for half in ['top','bottom']:
        icolor = 1
        grs[half] = []
        for y in range(1,6):
            num = 'clusterEOne_RandomSingles1_thetaY' + str(y) + half
            den = 'clusterEOne_Random_thetaY' + str(y) + half
            gr = getTriggerEfficiency(num, den, '-thetaYbins')
            gr.SetName(half + '_' + str(y))
            if half == 'top':
                c22.cd(1)
            else:
                c22.cd(2)
            if icolor==5:
                icolor = icolor + 1
            plotutils.setGraphStyle(gr,icolor)
            gr.Draw('same,LP')
            icolor = icolor + 1
            grs[half].append(gr)
    
    c22.cd(1)
    legt = plotutils.getLegendList(0.13,0.6,0.4,0.9,grs['top'], texts = [gr.GetName() for gr in grs['top']] ,styles = ['LP' for x in range(len(grs['top']))])
    legt.Draw()
    c22.cd(2)
    legb = plotutils.getLegendList(0.13,0.6,0.4,0.9,grs['bottom'], texts = [gr.GetName() for gr in grs['bottom']] ,styles = ['LP' for x in range(len(grs['bottom']))])
    legb.Draw()
    c22.SaveAs('trigEff-clusterEOne_RandomSingles1-overLay.png')

    ans = raw_input('cont?')

    
    for tFile in tFiles:
        tFile.Close()


