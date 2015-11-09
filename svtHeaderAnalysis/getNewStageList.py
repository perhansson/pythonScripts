import sys,re,os.path,math

path = '/scratch/'

f = open(sys.argv[1])



files_all = []
for l in f.readlines():
    #print l
    if 'hps_' not in l: continue
    run  = l.split()[0]
    i  = int(l.split()[1])
    logfile = os.path.basename(l.split()[2])
    #print logfile
    fname = logfile.split('.log')[0]
    if i > 4:
        j = int(math.floor(float(i)/5.0))
    else:
        j = 1
    files = [os.path.join(path,'hps_00%s.evio.%d'%(run,k)) for k in range(0,int(i),j)]
    files_all.extend(files)
    print run, ' ', i, ' ', files ,  ' ', fname
    
print 'all ',len(files_all), ' files'
print files_all
    

f.close()
