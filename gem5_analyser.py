import os
import re
import configparser
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
 
rootdir = 'output_final' # estas son 100x100, 50x50, 50x100*100x20, 128x50*50x20.
allowed_stats = ['sim_ticks', 'system.cpu.ipc',
                    'system.cpu.branchPred.condPredicted', 
                    'system.cpu.branchPred.condIncorrect']
MATRIX_BASELINE = [128, 50, 20]
BP_BASELINE = 'TournamentBP'
CACHE_SIZE_BASELINE = 8192
LOOP_UNROLLING_BASELINE = True
# Recibe dos listas desordenadas y correspondientes y las reordena
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
    print('Total folders ' , len(dirlist))
    return dirlist

    
def getTest(folder):
    config = configparser.ConfigParser()
    config.read(folder+'/config.ini')

    cmd=config['system.cpu.workload']['cmd']
    matrix_size = cmd.split(' ')
    if re.match('.*/blocked-matmul .*', config['system.cpu.workload']['cmd']):
        LOOP_UNROLLING = True
    else:
        LOOP_UNROLLING = False

    stats = {}
    filestat=open(folder + '/stats.txt','r')
    for line in filestat.readlines():
        line = re.split(' +', line) # cualquier cantidad de espacios
        if line[0] in allowed_stats:
            stats[line[0]] = line[1]


    return {'BP': config['system.cpu.branchPred']['type'],
         'LOOP_UNROLLING': LOOP_UNROLLING,
         'CacheSize': config['system.cpu.dcache.tags']['size'],
         'M_I':int(matrix_size[1]), 'M_J':int(matrix_size[2]), 'M_K':int(matrix_size[3]),
         'stats': stats}

def plotIPC(dataset, BP, LOOP_UNROLLING, I, J, K, file):
    # Data for plotting
    x = []
    y = []
    for data in dataset:
        if (data['BP'] == BP and data['M_I'] == I and data['M_J'] == J and data['M_K'] == K and data['LOOP_UNROLLING'] == LOOP_UNROLLING):
            x.append(int(data['CacheSize'])/1024)
            y.append(float(data['stats']['system.cpu.ipc']))

    x , y = sort(x,y)
    x = np.array(x)
    y = np.array(y)

    fig, ax = plt.subplots()
    ax.plot(x, y)
    loop = ' with -funroll-loops' if LOOP_UNROLLING else ' no optimization'
    ax.set(xlabel='Cache Size (Kb)', ylabel='IPC',
        title=('Matriz '+str(I)+'x'+str(J)+' X '+str(J)+'x'+str(K)+', '+ BP+ loop))
    ax.grid()

    fig.savefig(file)
    plt.show()

def plotBranchMiss(dataset, LOOP_UNROLLING, I, J, K, file):
    # data to plot
    n_groups = 8
    miss_rate = {'LocalBP':{},'BiModeBP':{},'TournamentBP':{}}
    miss_rate_list = {'LocalBP':[],'BiModeBP':[],'TournamentBP':[]}
    cachesizes = []
    #Populate Data
    for data in dataset:
        if (data['M_I'] == I and data['M_J'] == J and data['M_K'] == K and data['LOOP_UNROLLING'] == LOOP_UNROLLING):
            miss = int(data['stats']['system.cpu.branchPred.condPredicted'])/int(data['stats']['system.cpu.branchPred.condIncorrect']) * 100
            miss_rate[data['BP']][int(data['CacheSize'])/1024] = miss
    for key, data in miss_rate.items():
        sortDic = sorted(data.items())
        for ele in sortDic:
            if (key == BP_BASELINE ):
                cachesizes.append(ele[0])
            miss_rate_list[key].append(ele[1])
    # create plot
    fig, ax = plt.subplots()
    index = np.arange(n_groups)
    bar_width = 0.3
    opacity = 0.8
    
    rects1 = plt.bar(index, miss_rate_list['TournamentBP'], bar_width,
                    alpha=opacity,
                    color='b',
                    label='TournamentBP')
    
    rects2 = plt.bar(index + bar_width, miss_rate_list['BiModeBP'], bar_width,
                    alpha=opacity,
                    color='g',
                    label='BiModeBP')
    rects3 = plt.bar(index + bar_width*2, miss_rate_list['LocalBP'], bar_width,
                    alpha=opacity,
                    color='r',
                    label='LocalBP')

    loop = ' with -funroll-loops' if LOOP_UNROLLING else ' no optimization'
    plt.xlabel('Cache Size')
    plt.ylabel('Miss Rate Branch Predictor Percentage')
    plt.title('Matriz '+str(I)+'x'+str(J)+' X '+str(J)+'x'+str(K)+ loop)
    plt.xticks(index + bar_width, cachesizes)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(file)
    plt.show()

def main():
    dirlist = getFolders(rootdir)
    dataset = []

    for folder in  dirlist:
        dataset.append(getTest(folder))
    print('Total dataset len ' , len(dataset))

    ##Print all data
    # for data in dataset:
    #     print(data)

    # plotIPC(dataset, BP_BASELINE, LOOP_UNROLLING_BASELINE, MATRIX_BASELINE[0], MATRIX_BASELINE[1], MATRIX_BASELINE[2], 'IPC_loop.png') # tiene que existir el los folder
    # plotIPC(dataset, BP_BASELINE, False, MATRIX_BASELINE[0], MATRIX_BASELINE[1], MATRIX_BASELINE[2], 'IPC.png') # tiene que existir el los folder
    plotBranchMiss(dataset , True, MATRIX_BASELINE[0], MATRIX_BASELINE[1], MATRIX_BASELINE[2], 'MissBP_loop.png')
main()
