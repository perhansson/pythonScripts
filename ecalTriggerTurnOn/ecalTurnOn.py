#!/usr/bin/python

import os,sys,argparse,subprocess,re
from ROOT import TFile, TH2, TGraph2D, TCanvas, gStyle,TGraphAsymmErrors

debug = False


def getEffGr(hNum, hDen):

    gr = TGraphAsymmErrors()
    gr.Divide(hNum, hDen, 'cl=0.683 b(1,1) mode')
    return gr


    

if __name__ == '__main__':
    print 'just go'

    parser = argparse.ArgumentParser()
    parser.add_argument('-f',required=True, nargs=1,help='Input ROOT files')
    parser.add_argument('-d', action='store_true',help='debug')
    args = parser.parse_args()
    print args

    debug = args.d

    tfile = TFile(args.f[0])

    # find histograms
    num = 'clusterEOne_RandomSingles1'
    den = 'clusterEOne_Random'
    hNum = tfile.Get(num)
    hDen = tfile.Get(den)

    gr = getEffGr(hNum, hDen)

    c = TCanvas('c','c',10,10,700,500)
    c.Divide(1,2)
    c.cd(1)
    hNum.Draw()
    c.cd(2)
    hDen.Draw()

    c1 = TCanvas('c1','c1',10,10,700,500)
    gr.SetMarkerStyle(20)
    gr.SetMarkerSize(1.0)
    gr.Draw('AXP')

    ans = raw_input('cont?')
    

    tfile.Close()


