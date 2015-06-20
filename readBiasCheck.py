#!/usr/bin/python

import sys
import os
import argparse
import re
from ROOT import TFile, TH1D, TCanvas, TGraph
sys.path.append('pythonutils')
from plotutils import myText, setGraphStyle

def noise(files):
    if files==None:
        print 'No ROOT files'
        return
    c = TCanvas('cBiasCheck','cBiasCheck',10,10,700,500)
    c.Print(c.GetName() + '.ps[')
    grOnRMS = TGraph()
    grOnMean = TGraph()
    grOffRMS = TGraph()
    grOffMean = TGraph()
    for filename in files:
        f = TFile(filename)
        if f==None:
            print "couldnt open file ", filename
            return
        m = re.match('hps_00(\d+)\.\S+\.(\d+)\.root',os.path.basename(filename))
        if m==None:
            print ' this filename is weird' , filename
            sys.exit(1)
        run = m.group(1)
        runName = m.group(1)
        if m.group(2)!='':
            runName = run +  '.' + m.group(2)
        #hOffName = 'module_L1t_halfmodule_stereo_slot_sensor0 raw adc - ped maxSample>4 OFF'
        #hOnName = 'module_L1t_halfmodule_stereo_slot_sensor0 raw adc - ped maxSample>4 ON'
        #hOffName = 'module_L3t_halfmodule_stereo_sensor0 raw adc - ped maxSample>4 OFF'
        #hOnName = 'module_L3t_halfmodule_stereo_sensor0 raw adc - ped maxSample>4 ON'
        hOffName = 'module_L5t_halfmodule_stereo_slot_sensor0 raw adc - ped maxSample>4 OFF'
        hOnName = 'module_L5t_halfmodule_stereo_slot_sensor0 raw adc - ped maxSample>4 ON'
        hOff = f.Get(hOffName)
        hOn = f.Get(hOnName)
        if hOff!=None and hOn!=None:
            if hOn.GetEntries()>0:
                cOn = TCanvas('cBiasCheckOn %s'%runName,'cBiasCheckOn %s'%runName,10,10,700,500)
                hOn.SetFillColor(2)
                hOn.SetFillStyle(3003)
                hOn.Draw("hist")
                myText(0.2,0.7,'HV ON %s'%runName, 0.05,2)
                cOn.Print(c.GetName() + '.ps')
                grOnRMS.SetPoint(grOnRMS.GetN(),int(run), hOn.GetRMS())
                grOnMean.SetPoint(grOnMean.GetN(),int(run), hOn.GetMean())
            if hOff.GetEntries()>0:
                cOff = TCanvas('cBiasCheckOff %s'%runName,'cBiasCheckOff %s'%runName,10,10,700,500)
                hOff.SetFillColor(4)
                hOff.SetFillStyle(3003)
                hOff.Draw()
                myText(0.2,0.7,'HV OFF %s'%runName, 0.05,1)
                cOff.Print(c.GetName() + '.ps')
                grOffRMS.SetPoint(grOffRMS.GetN(),int(run), hOff.GetRMS())
                grOffMean.SetPoint(grOffMean.GetN(),int(run), hOff.GetMean())
            if hOn.GetEntries()>0 and hOff.GetEntries()>0:
                cOnOff = TCanvas('cBiasCheckOnOff %s'%runName,'cBiasCheckOnOff %s'%runName,10,10,700,500)
                hOn.SetLineColor(2)
                hOn.SetFillColor(2)
                hOn.SetFillStyle(3003)
                hOn.DrawNormalized("hist")
                hOff.DrawNormalized("same")
                myText(0.2,0.7,'HV ON %s'%runName, 0.05,2)
                myText(0.2,0.78,'HV OFF %s'%runName, 0.05,1)
                cOnOff.Print(c.GetName() + '.ps')
            #ans = raw_input('continue?')
        else:
            print 'couldnt get ', hOnName
    setGraphStyle(grOnMean)
    setGraphStyle(grOnRMS)
    setGraphStyle(grOffMean)
    setGraphStyle(grOffRMS)
    cGrOnMean = TCanvas('cGrOnMean','cGrOnMean',10,10,700,500)
    if grOnMean.GetN()>0:
        grOnMean.Draw('ALP')
        myText(0.2,0.7,'Mean HV ON', 0.05,1)
    cGrOnRMS = TCanvas('cGrOnRMS','cGrOnRMS',10,10,700,500)
    if grOnRMS.GetN()>0:
        grOnRMS.Draw('ALP')
        myText(0.2,0.7,'RMS HV ON', 0.05,1)
    cGrOffMean = TCanvas('cGrOffMean','cGrOffMean',10,10,700,500)
    if grOffMean.GetN()>0:
        grOffMean.Draw('ALP')
        myText(0.2,0.7,'Mean HV OFF', 0.05,1)
    cGrOffRMS = TCanvas('cGrOffRMS','cGrOffRMS',10,10,700,500)
    if grOffRMS.GetN()>0:
        grOffRMS.Draw('ALP')
        myText(0.2,0.7,'RMS HV OFF', 0.05,1)
    #ans = raw_input('continue?')
    cGrOnMean.Print(c.GetName() + '.ps')
    cGrOffMean.Print(c.GetName() + '.ps')
    cGrOnRMS.Print(c.GetName() + '.ps')
    cGrOffRMS.Print(c.GetName() + '.ps')
    c.Print(c.GetName() + '.ps]')

    return


def stats(files):
    if files==None:
        print 'no output files to process'
        return
    for filename in files:
        f = None
        try:
            f = open(filename,'r')
        except IOError:
            print "couldnt open file ", filename
            return 1
        for line in f.readlines():
            #print line
            m = re.search('.*eventCount\s(\d+)\seventCountHvOff\s(\d+)',line)
            if m!=None:
                print filename
                print line
                #print m.groups()
                n = m.group(1)
                nOff = m.group(2)
                print 'N=', n , ' nOff=', nOff
        f.close()

def main(args):

    print "GO main"
    noise(args.rootfiles)

    stats(args.files)



    return 0



if __name__ == "__main__":

    print "GO"

    parser = argparse.ArgumentParser(description='MP help script')
    parser.add_argument('-r','--rootfiles', nargs='+', help='List of ROOT files')
    parser.add_argument('-f','--files', nargs='+', help='List of files')
    parser.add_argument('-d','--debug', action='store_true', help='Debug flag')
    args = parser.parse_args()
    print args

    main(args)

    

