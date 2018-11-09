import os
import re
import configparser
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

rootdir = "output-example"
allowed_stats = ["sim_ticks", "system.cpu.ipc"]

def getFolders(rootdir):
    dirlist = []
    with os.scandir(rootdir) as rit:
        for entry in rit:
            if not entry.name.startswith('.') and entry.is_dir():
                dirlist.append(entry.path)

    dirlist.sort()
    return dirlist

    
def getTest(folder):
    config = configparser.ConfigParser()
    config.read(folder+"/config.ini")

    cmd=config['system.cpu.workload']['cmd']
    matrix_size = cmd.split(" ")

    stats = {}
    filestat=open(folder + "/stats.txt","r")
    for line in filestat.readlines():
        line = re.split(' +', line) # cualquier cantidad de espacios
        if line[0] in allowed_stats:
            stats[line[0]] = line[1]


    return {'BP': config['system.cpu.branchPred']['type'],
         'CacheSize': config['system.cpu.dcache.tags']['size'],
         "M_I":int(matrix_size[1]), "M_J":int(matrix_size[2]), "M_K":int(matrix_size[3]),
         'stats': stats}

def plotIPC(dataset, BP, I, J, K):
    # Data for plotting
    x = []
    y = []
    for data in dataset:
        if (data['BP'] == BP and data['M_I'] == I and data['M_J'] == J and data['M_K'] == K):
            x.append(int(data['CacheSize']))
            y.append(float(data['stats']['system.cpu.ipc']))


    x = np.array(x)
    y = np.array(y)

    fig, ax = plt.subplots()
    ax.plot(x, y)

    ax.set(xlabel='Cache Size (Kb)', ylabel='IPC',
        title=("Comparacion IPC con tamanno cache matriz "+str(I)+"x"+str(J)+" X "+str(J)+"x"+str(K)+" "+ BP))
    ax.grid()

    fig.savefig("IPC.png")
    plt.show()

def main():
    dirlist = getFolders("output-example")
    dataset = []

    for folder in  dirlist:
        dataset.append(getTest(folder))

    for data in dataset:
        print(data)

    plotIPC(dataset, 'TournamentBP', 4, 4, 4) # tiene que existir el los folder


main()
