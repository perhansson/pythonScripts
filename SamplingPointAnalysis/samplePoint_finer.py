import sys
import re
from ROOT import TCanvas,TH2F, TGraph2D

f = open(sys.argv[1],'r')


class Sync(object):
    def __init__(self,F,H,syncmap):
        self.F = F
        self.H = H
        self.syncmap = syncmap
        self.peakmap = None
        self.basemap = None
    



syncs = []
 
for line in f.readlines():
    h = line.rstrip('\n').split(':')[0]
    v = line.rstrip('\n').split(':')[1]
    print 'h \"', h, '\"'
    m = re.match('.*FebFpga\((\d)\).*',h)
    if m == None:
        print 'cannot find FEB for ', h
        sys.exit(1)
    F = int(m.group(1))

    m = re.match('.*HybridSyncStatus\((\d)\).*',h)
    if m == None:
        print 'cannot find hybrid for ', h
        sys.exit(1)
    H = int(m.group(1))

    print 'v \"', v, '\"'

    # find sync detected words
    v_sd = v.split('SyncDetected')[1].split('SyncPeak')[0]
    m = {}
    for pairs in v_sd.split(','):
        p = pairs
        if len(p.split()) <2:
            print 'skip \"',p,'\"'
            continue
        p_str = p.split()[0].replace(' ','')
        s_str = p.split()[1].replace(' ','')
        if not p_str:
            continue
        print 'p ', p_str
        phase = int(p_str)
        sync = int(s_str,0)
        m[phase] = sync    

    sync_obj = Sync(F,H,m)


    # find sync peak words
    v_p = v.split('SyncPeak')[1].split('SyncBase')[0]
    m_peak = {}
    for pairs in v_p.split(','):
        p = pairs
        if len(p.split()) <2:
            print 'skip \"',p,'\"'
            continue
        p_str = p.split()[0].replace(' ','')
        s_str = p.split()[1].replace(' ','')
        if not p_str:
            continue
        print 'p ', p_str
        phase = int(p_str)
        sync = int(s_str,0)
        if phase not in m_peak:
            m_peak[phase] = []
        m_peak[phase].append(sync)
    m_peak_ave = {}
    for p,vals in m_peak.iteritems():        
        v_ave = 0.
        for val in vals:
            v_ave += val
        v_ave = v_ave/len(vals)
        m_peak_ave[p] = v_ave
    
    sync_obj.peakmap = m_peak_ave

    # find sync base words
    v_p = v.split('SyncBase')[1]
    m_base = {}
    for pairs in v_p.split(','):
        p = pairs
        if len(p.split()) <2:
            print 'skip \"',p,'\"'
            continue
        p_str = p.split()[0].replace(' ','')
        s_str = p.split()[1].replace(' ','')
        if not p_str:
            continue
        print 'p ', p_str
        phase = int(p_str)
        sync = int(s_str,0)
        if phase not in m_base:
            m_base[phase] = []
        m_base[phase].append(sync)
    m_base_ave = {}
    for p,vals in m_base.iteritems():        
        v_ave = 0.
        for v in vals:
            v_ave += v
        v_ave = v_ave/len(vals)
        m_base_ave[p] = v_ave
    
    sync_obj.basemap = m_base_ave

    
    syncs.append( sync_obj )
    
    

print 'Got ', len(syncs), ' hybrids'

h_all = {}
c_all = []
for s in syncs:

    #if s.F != 0: continue
    if (s.F == 2 and s.H >1) or (s.F == 9 and s.H > 1):
        continue

    if s.F not in h_all:
        #h_all[s.F] = TH2F('h_all_feb_' + str(s.F),'FEB ' + str(s.F) +';SamplePoint;Hybrid',201,119.5,320.5,3,-0.5,3.5)
        h_all[s.F] = TGraph2D();
    

    h = h_all[s.F]
    h.SetTitle('FEB ' + str(s.F) + ' SyncDetected; ADC sample point; hybrid')
    h.SetMaxIter(1000)
    keys = s.syncmap.keys()
    keys.sort()
    for p in keys:
        #for p,v in s.syncmap.iteritems():
        v = s.syncmap[p]
        print 'F ', s.F,' p ', p, ' s.H ', s.H, ' v ', v
        #b = h.FindBin(p,s.H)
        #h.SetBinContent(b,v)
        h.SetPoint(h.GetN(),p,s.H,v)
    

for F in h_all.keys():
    c = TCanvas('c_' + str(F), 'c_' + str(F), 10,10,700,500)    
    c.SetTheta(90);
    c.SetPhi(0);   
    h_all[F].SetMarkerStyle(20)
    h_all[F].Draw('pcolz')
    c.SaveAs('samplepoint_finer_scan_feb_' + str(F) + '.png')
    c_all.append(c)
    ans = raw_input('continue?')



