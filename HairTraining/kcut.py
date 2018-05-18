import crash_on_ipy
import cPickle as pkl
from struct import pack
import sys
import metis_graph as mg
from local_para_small import *
import pymetis


if __name__ == "__main__":
    import os
    os.chdir(dumpFilePath)
    _g = pkl.load(file('mgA.dump'))
    nGroup = 10
    cut, vers = pymetis.part_graph(nGroup, xadj=_g.xadj, adjncy=_g.adjncy, eweights=_g.eweights)

    f = open("cg-"+str(nGroup)+".group","wb")
    import struct
    f.write(struct.pack('i', len(vers)))
    for i in vers:
        f.write(struct.pack('i', i))
    f.close()
