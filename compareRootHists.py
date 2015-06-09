#!/usr/bin/python

import sys, os
import argparse
from ROOT import TFile, gDirectory, TIter, TCanvas
from plotutils import myText, getLegend


def getHistograms(direc):
    histos = []
    print direc.GetList().GetSize()
    iter = TIter(direc.GetListOfKeys())
    print iter.GetCollection().GetSize(), ' items in collection'
    while True:
        key = iter.Next()
        if not key:
            break
        obj = key.ReadObj()
        if obj.InheritsFrom('TH1') and not obj.InheritsFrom('TH2') and not obj.InheritsFrom('TH3'):
            print 'Getting TH1 %s' % obj.GetName()
            histos.append(obj)
    print 'Got ', len(histos), ' TH1s'
    return histos

def main(file1,file2,legend=None,skip=None,only=None,skipempty=True,pause=False):
    print 'GO'

    f1 = TFile(file1)
    f1name = os.path.splitext(os.path.basename(file1))[0]
    histos1 = getHistograms(gDirectory)

    f2 = TFile(file2)
    f2name = os.path.splitext(os.path.basename(file2))[0]
    histos2 = getHistograms(gDirectory)

    n = 0
    nm = 0
    c = TCanvas('c_'+f1name+'_'+f2name,'c_'+f1name+'_'+f2name,10,10,700,500)
    #open file
    c.Print('cmp_' + f1name + '_' + f2name + '.ps[')
    for h1 in histos1:
        if skip != None:
            if skip in h1.GetName():
                continue
        if only != None:
            if only not in h1.GetName():
                continue
        print 'Look for ', h1.GetName()
        for h2 in histos2:
            if h1.GetName()==h2.GetName():            
                if skipempty:
                    if h1.GetEntries()==0.0 or h2.GetEntries()==0.0 or h1.Integral()==0.0 or h2.Integral()==0.0:
                        continue
                print 'match ', h1.GetName(), ' ',  h1.GetEntries(), ' ', h2.GetEntries()
                c = TCanvas('c_'+h1.GetName()+'_'+h2.GetName(),'c_'+h1.GetName()+'_'+h2.GetName(),10,10,700,500)
                h1.SetLineColor(4)
                h1.SetFillColor(4)
                h1.SetFillStyle(3004)
                h2.SetFillStyle(3005)
                h2.SetFillColor(2)
                h2.SetLineColor(2)
                h2.Scale(1.0/h2.Integral())
                h1.Scale(1.0/h1.Integral())
                if h1.GetMaximum()>h2.GetMaximum():
                    h1.Draw("hist")
                    h2.Draw("hist,same")
                else:
                    h2.Draw("hist")                    
                    h1.Draw("hist,same")
                #h1.DrawNormalized("hist",1.0/h1.Integral())
                #h2.DrawNormalized("same,hist",1.0/h2.Integral())
                n=n+1
                if legend:
                    l = getLegend(0.13,0.75,0.25,0.85,h1,h2,legend[0],legend[1],'FL','FL')
                    l.Draw()
                #c.SaveAs(c.GetName()+'.png')
                c.Print('cmp_' + f1name + '_' + f2name + '.ps')
                
                if pause:
                    ans = raw_input('press anywhere to continue')
            else:
                #print 'NO match ', h1.GetName()
                nm=nm+1
    print 'compared ', n, ' missed ', nm
    c.Print('cmp_' + f1name + '_' + f2name + '.ps]')
    

    f1.Close()
    f2.Close()
    return 0



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run comparison.')
    parser.add_argument('--files',nargs=2, required=True, help='Input files.')
    parser.add_argument('--skipempty',action='store_true', help='Input files.')
    parser.add_argument('--skip', help='Skip histogram containing this text.')
    parser.add_argument('--only', help='Use only histograms containing this text..')
    parser.add_argument('--pause', action='store_true',help='Pause b/w histograms')
    parser.add_argument('--legend',nargs=2,help='Legends to be used on plots.')
    args = parser.parse_args();
    print args
    
    #main(args)
    main(args.files[0],args.files[1],args.legend,args.skip,args.only,args.skipempty,args.pause)

