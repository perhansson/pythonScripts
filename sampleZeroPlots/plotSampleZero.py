#!/usr/bin/python

import os,sys,argparse,subprocess,re
from ROOT import TFile, TH2, TGraph2D, TCanvas, gStyle, TF1, TGraphErrors, gPad, gDirectory
sys.path.append('../pythonutils')
import compareRootHists
import plotutils
import hps_utils
debug = False
args = None

def getArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f','--file',required=True,help='Input ROOT files')
    parser.add_argument('-d','--debug', action='store_true',help='debug')
    parser.add_argument('--saveall', action='store_true',help='save all histograms')
    args = parser.parse_args()
    print args
    return args



def plot_sensor_hist(tFile,hist_name,half,maxminlist):
    names = hps_utils.get_module_names()    
    print 'found ', len(names), ' sensor names'
    graphBinNames = []
    graphMean = TGraphErrors()
    graphMean.SetName('grMean_' + half)
    graphRMS = TGraphErrors()
    graphRMS.SetName('grRMS_' + half)

    for h_name in [hist_name]:
        print 'Process histogram \"', h_name, '\"'
        for m_name in names:
            print 'Sensor \"', m_name, '\"'
            m_half = hps_utils.getHalf(m_name)            
            if half != '' and m_half != half:
                continue
            name = m_name + h_name 
            print 'Try to find histogram \"', name, '\"'
            h = t_file.Get(name)
            if h == None:
                print 'no histogram name \"', name, '\" found'
            else:
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
    c = TCanvas('c_' + hist_name +'_mean_'+half, 'c_' + hist_name +'_mean_'+half,10,10,1400,900)
    c.Divide(1,2)
    c.cd(1)
    gPad.SetBottomMargin(0.3)
    gPad.SetGridy()
    plotutils.setBinLabels(graphMean,graphBinNames)
    plotutils.setGraphStyle(graphMean)
    graphMean.SetTitle(hist_name+';;Mean')
    if len(maxminlist) == 4:
        graphMean.GetHistogram().SetMaximum(maxminlist[0])
        graphMean.GetHistogram().SetMinimum(maxminlist[1])
    graphMean.Draw('APL')
    c.cd(2)
    gPad.SetBottomMargin(0.3)
    gPad.SetGridy()
    plotutils.setBinLabels(graphRMS,graphBinNames)
    plotutils.setGraphStyle(graphRMS)    
    graphRMS.SetTitle(';;Width')
    if len(maxminlist) == 4:
        graphRMS.GetHistogram().SetMaximum(maxminlist[2])
        graphRMS.GetHistogram().SetMinimum(maxminlist[3])
    graphRMS.Draw('APL')
    c.SaveAs('summary_' + hist_name+'_mean_'+half+'.png')
    ans = raw_input('continue?')




def plot_sensor_hist_channel(tFile,run, hist_name, chlist, maxminlist):
    names = hps_utils.get_module_names()    
    print 'found ', len(names), ' sensor names'
    for h_name in [hist_name]:
        print 'Process histogram \"', h_name, '\"'
        for m_name in names:
            print 'Sensor \"', m_name, '\"'
            name = m_name + h_name 
            print 'Try to find histogram \"', name, '\"'
            h = t_file.Get(name)
            if h == None:
                print 'no histogram name \"', name, '\" found'
            else:
                graphBinNames = []
                graphMean = TGraphErrors()
                graphMean.SetName('grMean_' + m_name)
                graphRMS = TGraphErrors()
                graphRMS.SetName('grRMS_' + m_name)
                print 'got hist \"', h.GetName(), '\"'
                c = TCanvas('c_' + name, 'c_' + name,10,10,1400,900)
                for ch in chlist:
                    print 'Fit channel ', ch
                    c.Clear()
                    b = h.GetXaxis().FindBin(ch)
                    #print 'ch ', ch, ' -> bin ', b
                    hprj = h.ProjectionY(h.GetName() + '_prjy_' + str(ch), b, b, 'E')                    
                    if hprj.GetEntries() > 30:
                        fitFuncName = 'fg_' + hprj.GetName()
                        fitOpt = 'RQ'
                        fg = TF1(fitFuncName,'gaus')
                        bc = plotutils.getHistMaxBinValue(hprj)    
                        rms = hprj.GetRMS()
                        fg.SetParameter(1,bc)                
                        fg.SetParameter(2,rms)                
                        fg.SetRange( bc - rms*1.5, bc + rms*1.5 )
                        hprj.Fit(fg,fitOpt)
                        #print 'make graphs of mean and RMS'
                        mean = fg.GetParameter(1)
                        meanError = fg.GetParError(1)
                        rms = fg.GetParameter(2)
                        rmsError = fg.GetParError(2)
                        if meanError > 10.:
                            print 'meanError ', meanError, ' large -> skip this channel, '
                            continue
                        if rmsError > 10.:
                            print 'rmsError ', rmsError, ' large -> skip this channel, '
                            continue
                        ipoint = graphMean.GetN()
                        graphMean.SetPoint(ipoint, ch, mean)
                        graphRMS.SetPoint(ipoint, ch, rms)
                        graphMean.SetPointError(ipoint, 0., meanError)
                        graphRMS.SetPointError(ipoint, 0., rmsError)
                        #print 'mean ', mean, '+-',meanError,' RMS ', rms, '+-', rmsError, ' fg ', fg.GetName()
                    else:
                        print 'Not enough entries for histogram \"', name, '\"'
                    hprj.Draw()
                    if args.saveall:
                        c.SaveAs('run_' + str(run) + '_' + name + '_ch' + str(ch) + '.png')
                    #ans = raw_input('continue?')
            c = TCanvas('c_' + name +'_mean', 'c_' + name +'_mean',10,10,1400,900)
            c.Divide(1,2)
            c.cd(1)
            gPad.SetBottomMargin(0.3)
            gPad.SetGridy()
            #print 'get template for mean '
            #h_temp_mean = plotutils.getTemplate(graphMean,graphBinNames)
            #plotutils.setBinLabels(graphMean,graphBinNames)
            plotutils.setGraphStyle(graphMean)
            graphMean.SetTitle(name + ';Channel;Mean')
            if len(maxminlist) == 4:
                graphMean.GetHistogram().SetMaximum(maxminlist[0])
                graphMean.GetHistogram().SetMinimum(maxminlist[1])
            #h_temp_mean.Draw()
            graphMean.Draw('APL')
            graphMean.SaveAs(plotutils.fixSaveName('run_' + str(run) + '_summary_' + name + '_mean.root'))
            
            c.cd(2)
            gPad.SetBottomMargin(0.3)
            gPad.SetGridy()
            #print 'get template for mean '
            #h_temp_rms = plotutils.getTemplate(graphRMS,graphBinNames)
            #plotutils.setBinLabels(graphRMS,graphBinNames)
            plotutils.setGraphStyle(graphRMS)    
            graphRMS.SetTitle(name + ';Channel;Width')
            if len(maxminlist) == 4:
                graphRMS.GetHistogram().SetMaximum(maxminlist[2])
                graphRMS.GetHistogram().SetMinimum(maxminlist[3])
            #h_temp_rms.Draw()
            graphRMS.Draw('APL')
            graphRMS.SaveAs(plotutils.fixSaveName('run_' + str(run) + '_summary_' + name + '_rms.root'))
            c.SaveAs(plotutils.fixSaveName('run_' + str(run) + '_summary_' + name + '_rms.png'))
            #ans = raw_input('continue?')






if __name__ == '__main__':
    print 'just go'

    args = getArgs()

    debug = args.debug

    t_file = TFile(args.file)    
    #plot_sensor_hist(t_file,' - first sample (MAX_SAMPLE>=4)','t',[])
    #plot_sensor_hist(t_file,' - first sample (MAX_SAMPLE>=4)','b',[])
    
    channel_list = range(1,640)
    run = hps_utils.get_run_from_filename(args.file)
    plot_sensor_hist_channel(t_file, run,' channels - first sample (MAX_SAMPLE>=4)', channel_list, [])
    
    t_file.Close()


