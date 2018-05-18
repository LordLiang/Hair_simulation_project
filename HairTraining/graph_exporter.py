import crash_on_ipy
import cPickle as pkl
from struct import pack
import sys
import metis_graph as mg
from local_para import *


if __name__ == "__main__":
    from local_para import *
    import os
    os.chdir(dumpFilePath)
    fileName = dumpedmgA
    exportName = sys.argv[1]
    assert(exportName != "")

    G = pkl.load(file(fileName))

    with open(exportName, 'wb') as output:
        output.write(pack('i', len(G.eweights)/2))
        output.write(pack('i', nStep))
        edgeItr = mg.UndirectedIterator(G)
        for edge in edgeItr:
            output.write(pack('i', edge[0]))
            output.write(pack('i', edge[1]))
            output.write(pack('i', edge[2]))
