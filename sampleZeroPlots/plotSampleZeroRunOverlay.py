#!/usr/bin/python

import os,sys,argparse,subprocess,re
from ROOT import TFile, TH2, TGraph2D, TCanvas, gStyle, TF1, TGraphErrors, gPad, gDirectory, TLegend
sys.path.append('../pythonutils')
import compareRootHists
import plotutils
import hps_utils
debug = False
args = None

def getArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f','--files',nargs='+',required=True,help='Input ROOT files')
    parser.add_argument('-d','--debug', action='store_true',help='debug')
    args = parser.parse_args()
    print args
    return args




def plotGraphs(graphs, name):

    print 'plot ', len(graphs)

    c = TCanvas('c_' + name, 'c_' + name, 10, 10, 1400, 900)
    legend = TLegend(0.75,0.67,0.95,0.88)
    legend.SetFillColor(0)
    for i in range( len(graphs) ):
        gr = graphs[i].graph
        run = graphs[i].run
        print 'plot graph \"', gr.GetName(), '\" for run ', run

        gr.SetMarkerColor(1+i)
        gr.SetLineColor(1+i)
        gr.SetMarkerSize(1.)

        if( i == 0 ):
            gr.Draw('ALP')
        else:
            gr.Draw('LP,same')
        legend.AddEntry(gr,str(run),'LP')
    legend.Draw()
    saveName = ''
    for gr in graphs:
        saveName += str(gr.run) + '_'
    c.SaveAs(saveName + '_' + name + '_overlay.png')
    #ans = raw_input('continue?')


def plotGraphRatios(graphs, name):

    print 'plot ratios for ', len(graphs), ' graphs'
    if len(graphs) < 2:
        print 'error'
        sys.exit(1)
    

    c = TCanvas('c_ratio_' + name , 'c_ratio' + name, 10, 10, 1400, 900)
    legend = TLegend(0.75,0.67,0.95,0.88)
    legend.SetFillColor(0)
    grDen = None
    runDen = -1
    for i in range( len(graphs) ):
        gr = graphs[i].graph
        run = graphs[i].run
        print 'plot ration graph \"', gr.GetName(), '\" for run ', run

        if i == 0 :
            grDen = gr
            runDen = run
        else:
            grRatio = plotutils.divideTGraphs(gr,grDen)
            grRatio.SetTitle('ratio ' + gr.GetName())
            grRatio.GetXaxis().SetTitle('Channel')
            grRatio.GetYaxis().SetTitle('Ratio')
            grRatio.SetMarkerColor(1+i)
            grRatio.SetLineColor(1+i)
            grRatio.SetMarkerSize(1.)
            grRatio.SetMarkerStyle(20)

            if i == 1:
                grRatio.Draw('ALP')
            else:
                grRatio.Draw('LP,same')
            
            legend.AddEntry(grRatio,str(run)+'/'+str(runDen),'LP')

    legend.Draw()
    saveName = ''
    for gr in graphs:
        saveName += str(gr.run) + '_'
    c.SaveAs(saveName + '_' + name + '_overlay_ratio.png')
    #ans = raw_input('continue?')

        




class ModuleGraph:
    def __init__(self,run,name, graph):
        self.run = run
        self.name = name
        self.graph = graph

if __name__ == '__main__':
    print 'just go'

    args = getArgs()

    debug = args.debug

    graphs = []

    # get list of all modules
    names = hps_utils.get_module_names()

    for f in args.files:

        module_name = ''
        for name in names:
            if name in f:
                module_name = name
                break

        print 'module name ', module_name

        if 'rms' in f:
            graph_name = 'grRMS_' + module_name
        else:
            graph_name = 'grMean_' + module_name

        print ' graph name ', graph_name
        
        run = hps_utils.get_run_from_filename(f)

        print 'run ', run

        t_file = TFile(f)
        
        graph = t_file.Get( graph_name )

        #graph.SetDirectory(None)
        
        t_file.Close()

        if graph == None:
            print ' can not find graph \"', graph_name, '\" for file \"', f , '\"' 
            continue

        mg = ModuleGraph(run,module_name, graph)
        graphs.append(mg)



    print 'Found ', len(graphs), ' ModuleGraphs in ', len(args.files), ' files'



    for gr in graphs:
        # find the others and overlay
        grs = []
        runs = []
        grs.append(gr)
        for gr2 in graphs:
            if gr.run == gr2.run:
                continue
            if gr.name == gr2.name:
                grs.append(gr2)
        
        print 'overlay ', len(grs), ' graphs'
        
        plotGraphs(grs, gr.graph.GetName())
        plotGraphRatios(grs, gr.graph.GetName())

