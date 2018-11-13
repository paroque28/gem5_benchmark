import os
import re
import configparser
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
 
rootdir = "output_final" # estas son 100x100, 50x50, 50x100*100x20, 128x50*50x20.
allowed_stats = ["sim_ticks", "system.cpu.ipc"]
MATRIX_BASELINE = [128, 50, 20]
BP_BASELINE = 'TournamentBP'
CACHE_SIZE_BASELINE = 8192
LOOP_UNROLLING_BASELINE = False

def sort(x,y):
    assert(len(x)==len(y))
    data = {}
    for i in range (len(x)):
        data[x[i]]=y[i]
    data = sorted(data.items())
    x = []
    y = []
    for d in data:
        x.append(d[0])
        y.append(d[1])
    return x , y
def getFolders(rootdir):
    dirlist = []
    with os.scandir(rootdir) as rit:
        for entry in rit:
            if not entry.name.startswith('.') and entry.is_dir():
                dirlist.append(entry.path)

    dirlist.sort()
    print("Total folders " , len(dirlist))
    return dirlist

    
def getTest(folder):
    config = configparser.ConfigParser()
    config.read(folder+"/config.ini")

    cmd=config['system.cpu.workload']['cmd']
    matrix_size = cmd.split(" ")
    if re.match('.*/blocked-matmul .*', config['system.cpu.workload']['cmd']):
        LU = True
    else:
        LU = False

    stats = {}
    filestat=open(folder + "/stats.txt","r")
    for line in filestat.readlines():
        line = re.split(' +', line) # cualquier cantidad de espacios
        if line[0] in allowed_stats:
            stats[line[0]] = line[1]


    return {'BP': config['system.cpu.branchPred']['type'],
         'LU': LU,
         'CacheSize': config['system.cpu.dcache.tags']['size'],
         "M_I":int(matrix_size[1]), "M_J":int(matrix_size[2]), "M_K":int(matrix_size[3]),
         'stats': stats}

def plotIPC(dataset, BP, LU, I, J, K):
    # Data for plotting
    x = []
    y = []
    for data in dataset:
        if (data['BP'] == BP and data['M_I'] == I and data['M_J'] == J and data['M_K'] == K and data["LU"] == LU):
            x.append(int(data['CacheSize'])/1024)
            y.append(float(data['stats']['system.cpu.ipc']))

    x , y = sort(x,y)
    x = np.array(x)
    y = np.array(y)

    fig, ax = plt.subplots()
    ax.plot(x, y)

    ax.set(xlabel='Cache Size (Kb)', ylabel='IPC',
        title=("IPC contra tamaño cache, matriz "+str(I)+"x"+str(J)+" X "+str(J)+"x"+str(K)+", "+ BP))
    ax.grid()

    fig.savefig("IPC.png")
    plt.show()

def main():
    dirlist = getFolders(rootdir)
    dataset = []

    for folder in  dirlist:
        dataset.append(getTest(folder))
    print("Total dataset len " , len(dataset))

    ##Print all data
    for data in dataset:
        print(data)

    #plotIPC(dataset, BP_BASELINE, LOOP_UNROLLING_BASELINE, MATRIX_BASELINE[0], MATRIX_BASELINE[1], MATRIX_BASELINE[2]) # tiene que existir el los folder

main()
