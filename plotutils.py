import sys
from ROOT import TLatex, TLegend, gDirectory, TIter, TCanvas, Double


def myText(x,y,text, tsize,color):
    l = TLatex()
    l.SetTextSize(tsize); 
    l.SetNDC();
    l.SetTextColor(color);
    l.DrawLatex(x,y,text);


def getLegend(x1,y1,x2,y2,h1,h2,txt1,txt2,style1,style2):
    l = TLegend(x1,y1,x2,y2)
    l.SetFillColor(0)
    l.SetFillStyle(0)
    l.SetBorderSize(0)
    l.AddEntry(h1,txt1,style1)
    l.AddEntry(h2,txt2,style2)
    return l

def getLegendList(x1,y1,x2,y2,histos,texts,styles):
    l = TLegend(x1,y1,x2,y2)
    l.SetFillColor(0)
    l.SetFillStyle(0)
    l.SetBorderSize(0)
    for i in range(len(histos)):
        h = histos[i]
        txt = texts[i]
        style = styles[i]
        l.AddEntry(h,txt,style)
    return l

def setGraphStyle(gr,color=1):
    gr.SetMarkerStyle(20)
    gr.SetMarkerSize(1.0)
    gr.SetMarkerColor(color)
    gr.SetLineColor(color)


def setBinLabels(gr,names):
    h = gr.GetHistogram()
    print h.GetNbinsX(), ' vs ', gr.GetN()
    i = 0
    for p in names:
        b = h.FindBin(i)
        h.GetXaxis().SetBinLabel(b, p )
        i = i + 1

def setBinLabelsDict(gr,namePoints):
    h = gr.GetHistogram()
    print h.GetNbinsX(), ' vs ', gr.GetN()
    for i,p in namePoints.iteritems():
        b = h.FindBin(i)
        h.GetXaxis().SetBinLabel(b, p )

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


def getGraphMaxMinVal(gr):
    ymax = -999999.9
    ymin = 999999.9
    for ipoint in range(gr.GetN()):
        x = Double(0.0)
        y = Double(0.0)
        gr.GetPoint(ipoint,x,y)
        if y > ymax:
            ymax = y
        if y < ymin:
            ymin = y
    return [ymin, ymax]



        
