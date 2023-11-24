"""
Useful Lattice Methods for dealing with Chroma XML files.
"""

import os
import math
import xml.etree.ElementTree as ET
import numpy as np
import pickle
import time
from tqdm import tqdm
import os

defaults = {}
for x in open('xml_defaults/xml.txt').read().split('\n\n'):
    y = finv(x,'Name:{Name}\nTags:{Tags}\nDescription:{Description}\nData:\n{Data}',capture_newline=True)
    defaults[y['Name']] = y

def write_xml(meas_list, lattice_size, cfg_type=None,
              filehead=None,cfg=None,filetail=None,write=None):
    """
    Inputs:
      meas_list : [meas]
        meas : {('Name',i) ∈ {QIO_READ_NAMED_XML,...},
            'NoniterableName' : Some fixed string,
            'IterableName' : [val1,val2,...],
            'Iterable*Name' : [wal1,wal2,...],...}
      lattice_size : (x,y,z,t)
      cfg_type     ∈ {UNIT,WEAK_FIELD,NERSC}
      type(filehead) is type(filetail) is str
      cfg          : [int]

      write : if provided, writes to this. Include more documentation here.
    Returns:
      XML file.

    If cfg_type is NERSC, then we are left with an XML file which needs you to replace
    JRfileheadJRcfgJRfiletail.
    (iterable*) means that it will be iterated over, but creating a new measurement for
    each choice of parameters, and they are streamed together
    (iterable) means that it is iterated within a single measurement, and is one-shot
    (Name,i) means that it will be iterated over, creating a new measurement for each
    choice of parameters, and they are collated, over all measurements with same i
    """

    to_return = """<?xml version="1.0"?><chroma><Param><InlineMeasurements>"""
    to_collate = {}
    collate_idx = None
    for x in meas_list:
        #Check if we need to finish a collate step
        if (collate_idx is not None) and \
               ((type(x['Name']) is tuple and x['Name'][1] is not collate_idx) or \
                (type(x['Name']) is not tuple)):
            to_return += "".join(["".join(x) for x in zip(to_collate[collate_idx])])

        #Check if we need to collate this measurement against others
        if type(x['Name']) is tuple:
            if collate_idx is not x['Name'][1]:
                to_collate[x['Name'][1]] = []
            collate_idx = x['Name'][1]
            meas = defaults[x['Name'][0]]['Data']
            tags = defaults[x['Name'][0]]['Tags'].split(',')
        else:
            collate_idx = None
            meas = defaults[x['Name']]['Data']
            tags = defaults[x['Name']]['Tags'].split(',')

        #Check that we have what we need to replace the things that need to be replaced
        if set(tags) != set([k for k in x.keys() if k != 'Name']):
            print("You haven't replaced the right fields. You need to replace:")
            print(set(tags))
            print("And you currently have tried to replace")
            print(set([k for k in x.keys() if k != 'Name']))
            raise
            
        #Go through and replace what needs to be replaced
        iterkeys = []
        itervals = []
        for k in x.keys():
            if k == 'Name':
                continue
            if type(x[k]) is str:
                #noniterable
                meas = meas.replace(f"{{{k}}}",x[k])
            elif type(x[k]) is list:
                #Foliated
                iterkeys.append(k)
                itervals.append(x[k])

        if len(iterkeys) == 0:
            to_return += meas
        else:
            temp_list = []
            for y in zip(*itervals):
                temp = meas
                for i in range(len(iterkeys)):
                    temp = temp.replace(f'{{{iterkeys[i]}}}',y[i])
                if collate_idx is None:
                    to_return += temp
                else:
                    temp_list.append(temp)
            if collate_idx is not None:
                to_collate[collate_idx].append(temp_list)
            else:
                to_return += "".join(temp_list)
    if collate_idx is not None:
        to_return += "".join(["".join(x) for x in zip(*to_collate[collate_idx])])
    tail = """</InlineMeasurements><nrow>{lattice_size}</nrow></Param>
              <RNG><Seed><elem>11</elem><elem>11</elem><elem>11</elem><elem>0</elem></Seed></RNG>
              <Cfg><cfg_type>{cfg_type}</cfg_type><cfg_file>{filehead}{cfg}{filetail}</cfg_file>
              </Cfg></chroma>"""
    to_return += tail.replace(f'{{lattice_size}}'," ".join([str(x) for x in lattice_size]))
    if cfg_type is not None:
        to_return = to_return.replace(f"{{cfg_type}}",cfg_type)
        to_return = to_return.replace(f"{{filehead}}","").replace(f"{{{filetail}}}","")
        to_return = to_return.replace(f"{{cfg}}","dummy")
        return [to_return]
    else:
        to_return = to_return.replace(f"{{cfg_type}}",'NERSC')
        to_return = to_return.replace(f"{{filehead}}",filehead).replace(f"{{filetail}}",filetail)
        if write is not None:
            for x in cfg:
                opf = open(write+"_"+str(x),"w")
                opf.write(to_return.replace(f"{{cfg}}",str(x)))
                opf.close()
        return (to_return.replace(f"{{cfg}}",x) for x in cfg)

def gen_run(chroma,
            inidir,
            outdir,
            logdir,
            rundir,
            split,
            qos="regular",
            account="m789",
            constraint="knl",
            time="04:00:00",
            nodes="1",
            dry=True):
    base = f"""#!/bin/bash
#SBATCH --qos=JRqos
#SBATCH --account={account}
#SBATCH --constraint={constraint}
#SBATCH --time=JRtime
#SBATCH --nodes={nodes}

export OMP_NUM_THREADS=256
module load openmpi
CHROMA="{chroma}"
"""
    ld = os.listdir(inidir)
    chunk = math.ceil(len(ld)/split)
    for j in range(split):
        temp = base
        for i in range(j*chunk,(j+1)*chunk if j < split - 1 else len(ld)-1):
            
            temp += f"srun $CHROMA -by 8 -bz 8 -c 256 -sy 1 -sz 1 -geom 1 1 1 1 -ldims 16 16 16 16 -bdims 2 2 2 2 -nvec 24 -i {inidir}/{ld[i]} -o {outdir}/{ld[i]}\n\n"# > {logdir}/{ld[i]}\n"
        f = open(f"{rundir}/{j}.run","w")
        f.write(temp.replace("JRtime",time).replace("JRqos",qos))
        f.close()
        
        if j == 0 and dry:
            f = open(f"{rundir}/0.dryrun","w")
            f.write(temp.replace("JRtime","00:30:00").replace("JRqos","debug"))
            f.close()
        
                    
            
        

