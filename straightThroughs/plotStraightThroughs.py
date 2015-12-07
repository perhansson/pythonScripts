#!/usr/bin/python

import os,sys,argparse,subprocess,re
from ROOT import TFile, TH2, TGraph2D, TCanvas, gStyle, TF1, TGraphErrors, gPad, gDirectory
sys.path.append('../pythonutils')
import compareRootHists
import plotutils
import hps_utils
debug = False



def get_module_names():
    
    names = []
    for l in range(1,7):
        for h in ['t','b']:
            for t in ['axial','stereo']:
                if l < 4:
                    name = 'module_L' + str(l) + h +'_halfmodule_' + t + '_sensor0'
                    names.append(name)
                else:
                    for s in ['hole','slot']:
                        name = 'module_L' + str(l) + h +'_halfmodule_' + t + '_' + s + '_sensor0'
                        names.append(name)
    return names


def plot_residuals(tFile,hist_name,half,side,maxminlist):
    #module_L6b_halfmodule_axial_hole_sensor0_hitresglobal
    #module_L1t_halfmodule_axial_sensor0_hitresglobal
    names = get_module_names()    
    print 'found ', len(names), ' histogram names'
    graphBinNames = []
    graphMean = TGraphErrors()
    graphMean.SetName('grMean_' + half)
    graphRMS = TGraphErrors()
    graphRMS.SetName('grRMS_' + half)

    for h_name in [hist_name]:
        for m_name in names:
            m_half = hps_utils.getHalf(m_name)            
            if half != '' and m_half != half:
                continue
            if hps_utils.getAxialStereo(m_name) == 'stereo':
                continue
            if hps_utils.getLayer(m_name) > 3:
                if side != '' and hps_utils.getHoleSlot(m_name) != side:
                    continue
            name = m_name + '_' + h_name 
            h = t_file.Get(name)
            if h == None:
                print 'no histogram name \"', name, '\" found'
            print 'got hist \"', h.GetName(), '\"'
            c = TCanvas('c_' + name, 'c_' + name,10,10,1400,900)
            if h.GetEntries() > 10:
                fitFuncName = 'fg_' + h.GetName()
                fitOpt = 'R'
                fg = TF1(fitFuncName,'gaus')
                bc = plotutils.getHistMaxBinValue(h)    
                rms = h.GetRMS()
                fg.SetParameter(1,bc)                
                fg.SetParameter(2,rms)                
                fg.SetRange( bc - rms*2, bc + rms*2 )
                h.Fit(fg,fitOpt)
                #print 'make graphs of mean and RMS'
                mean = fg.GetParameter(1)
                meanError = fg.GetParError(1)
                rms = fg.GetParameter(2)
                rmsError = fg.GetParError(2)
                ipoint = graphMean.GetN()
                graphMean.SetPoint(ipoint, ipoint, mean)
                graphRMS.SetPoint(ipoint, ipoint, rms)
                graphMean.SetPointError(ipoint, 0., meanError)
                graphRMS.SetPointError(ipoint, 0., rmsError)
                graphBinNames.append(hps_utils.getshortsensorname( m_name ) )
                print 'mean ', mean, '+-',meanError,' RMS ', rms, '+-', rmsError, ' fg ', fg.GetName()
            else:
                print 'Not enough entries for histogram \"', name, '\"'
            h.Draw()
            #ans = raw_input('continue?')
            saveName = name
            c.SaveAs(saveName + '.png')
    c = TCanvas('c_' + hist_name +'_mean_'+half+'_'+side, 'c_' + hist_name +'_mean_'+half+'_'+side,10,10,1400,900)
    c.Divide(1,2)
    c.cd(1)
    gPad.SetBottomMargin(0.3)
    gPad.SetGridy()
    plotutils.setBinLabels(graphMean,graphBinNames)
    plotutils.setGraphStyle(graphMean)
    graphMean.SetTitle(hist_name+';;Track residual mean (mm)')
    if len(maxminlist) == 4:
        graphMean.GetHistogram().SetMaximum(maxminlist[0])
        graphMean.GetHistogram().SetMinimum(maxminlist[1])
    graphMean.Draw('APL')
    c.cd(2)
    gPad.SetBottomMargin(0.3)
    gPad.SetGridy()
    plotutils.setBinLabels(graphRMS,graphBinNames)
    plotutils.setGraphStyle(graphRMS)    
    graphRMS.SetTitle(';;Axial track residual width (mm)')
    if len(maxminlist) == 4:
        graphRMS.GetHistogram().SetMaximum(maxminlist[2])
        graphRMS.GetHistogram().SetMinimum(maxminlist[3])
    graphRMS.Draw('APL')
    c.SaveAs('summary_' + hist_name+'_mean_'+half+'_'+side +'.png')
    ans = raw_input('continue?')



def plot_projection(t_file, hist_name):
    h = t_file.Get(hist_name)
    c = TCanvas('c_extrapol','c_extrapol',10,10,1400,900)
    c.Divide(1,3)
    c.cd(1)
    h.Draw('colz')
    h.FitSlicesY(0,5,25,10)
    hM = gDirectory.Get(h.GetName()+'_1')
    if hM == None:
        print 'no slice 1 histo found'
    else:
        c.cd(2)
        hM.Draw()
    hW = gDirectory.Get(h.GetName()+'_2')
    if hW == None:
        print 'no slice 2 histo found'
    else:
        c.cd(3)
        hW.Draw()
        f = TF1('fpol2','pol2',h.GetXaxis().GetBinCenter(6),h.GetXaxis().GetBinCenter(24))
        hW.Fit(f,'R')
        min_val = f.GetParameter(1)/(-2.0*f.GetParameter(2))
        plotutils.myText(0.5,0.5,'min_val=%.0f mm' % min_val,0.07,2)
        
    ans = raw_input('continue?')
    c.Update()
    c.SaveAs(hist_name.replace(' ','_') + '.png')

if __name__ == '__main__':
    print 'just go'

    parser = argparse.ArgumentParser()
    parser.add_argument('--file',required=True,help='Input ROOT files')
    parser.add_argument('--debug', action='store_true',help='debug')
    args = parser.parse_args()
    print args

    debug = args.debug

    t_file = TFile(args.file)
    

    #plot_residuals(t_file,'hitresglobal','t','hole',[0.07,-0.07,0.16,0.0])
    #plot_residuals(t_file,'hitresglobal','b','hole',[0.03,-0.03,0.16,0.0])

    #plot_residuals(t_file,'stereohitxzresglobal','t','hole',[0.4,-0.4,0.3,0.0])
    #plot_residuals(t_file,'stereohitxzresglobal','b','hole',[0.4,-0.4,0.3,0.0])

    #plot_residuals(t_file,'stereohityzresglobal','t','hole',[0.07,-0.07,0.16,0.0])
    #plot_residuals(t_file,'stereohityzresglobal','b','hole',[0.03,-0.03,0.16,0.0])

    #plot_projection(t_file,'Track axial extrapolation')
    plot_projection(t_file,'Track extrapolation Y')
    plot_projection(t_file,'Track extrapolation X')

    t_file.Close()

