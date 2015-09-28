#!/usr/bin/python

import os,sys,argparse,subprocess,re
from ROOT import TFile, TH2F, TGraph2D, TCanvas, gStyle,TGraphAsymmErrors
sys.path.append('../')
import plotutils

debug = False


def getEffGr(hNum, hDen):

    gr = TGraphAsymmErrors()
    gr.Divide(hNum, hDen, 'cl=0.683 b(1,1) mode')
    gr.SetMarkerStyle(20)
    gr.SetMarkerSize(1.0)
    return gr



tfile = TFile(sys.argv[1])

# find histograms
num = 'clusterEOne_RandomSingles1'
den = 'clusterEOne_Random'
hNum = tfile.Get(num)
hDen = tfile.Get(den)
gr = getEffGr(hNum, hDen)

c1 = TCanvas('c1','c1',10,10,700,500*2)
c1.Divide(1,3)
c1.cd(1)
hNum.Draw()
c1.cd(2)
hDen.Draw()
c1.cd(3)
#gr.SetMarkerStyle(20)
#gr.SetMarkerSize(1.0)
gr.Draw('AP')
c1.SaveAs('trigEff-clusterEOne_RandomSingles1.png')
ans = raw_input('sd')


hNumSum = None
hDenSum = None

cs = []
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

for half in ['top','bottom']:
    icolor = 1
    grs[half] = []
    for y in range(1,6):
        num = 'clusterEOne_RandomSingles1_thetaY' + str(y) + half
        den = 'clusterEOne_Random_thetaY' + str(y) + half
        hNum = tfile.Get(num)
        hDen = tfile.Get(den)
        print hNum.GetName()
        print hDen.GetName()

        if hNumSum == None:
            hNumSum = hNum.Clone(hNum.GetName() + '_sum')
            hDenSum = hDen.Clone(hDen.GetName() + '_sum')
        else:
            hNumSum.Add(hNum)
            hDenSum.Add(hDen)
        
        gr = getEffGr(hNum, hDen)
        gr.SetName(half + '_' + str(y))

        cName = 'c_' + half + '_' + str(y)
        c = TCanvas(cName,cName,10,10,700,500*2)
        c.Divide(1,3)
        c.cd(1)
        hNum.Draw()
        c.cd(2)
        hDen.Draw()
        c.cd(3)
        gr.Draw('AP')        
        c.SaveAs('trigEff-clusterEOne_RandomSingles1_thetaY' + str(y) + '_' + half + '.png')

        if half == 'top':
            c22.cd(1)
        else:
            c22.cd(2)

        if icolor==3:
            icolor = icolor + 1
        plotutils.setGraphStyle(gr,icolor)
        gr.Draw('same,LP')
        icolor = icolor + 1

        grs[half].append(gr)
        cs.append(c)


c22.cd(1)
legt = plotutils.getLegendList(0.13,0.6,0.4,0.9,grs['top'], texts = [gr.GetName() for gr in grs['top']] ,styles = ['LP' for x in range(len(grs['top']))])
legt.Draw()
c22.cd(2)
legb = plotutils.getLegendList(0.13,0.6,0.4,0.9,grs['bottom'], texts = [gr.GetName() for gr in grs['bottom']] ,styles = ['LP' for x in range(len(grs['bottom']))])
legb.Draw()
c22.SaveAs('trigEff-clusterEOne_RandomSingles1-overLay.png')


gr = getEffGr(hNumSum, hDenSum)
cName = 'c_sum'
c2 = TCanvas(cName,cName,10,10,700,500*2)
c2.Divide(1,3)
c2.cd(1)
hNumSum.Draw()
c2.cd(2)
hDenSum.Draw()
c2.cd(3)
gr.Draw('AP')
c.SaveAs('trigEffsum-clusterEOne_RandomSingles1.png')


ans = raw_input('cont?')


tfile.Close()


