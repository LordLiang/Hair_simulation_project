
# file1 = "E:/cache/329.xml"
# file2 = "../../maya cache/03074/hair_nRigidShape1.xml"
# file3 = "E:/c0418.xml"
# file3 = "D:/424.xml"

if __name__ == "__main__":

    import time
    import sys

    starttime = time.strftime('%Y-%m-%d  %Hh%Mm%Ss',time.localtime(time.time()))
    print "start at:", starttime

    import crash_on_ipy
    import numpy as np
    np.set_printoptions(suppress=True)

    needLoad = False
    import getopt
    try:
        (opts, args) = getopt.getopt(sys.argv[1:], "f:")
    except getopt.error:
        print "No dump data specified"

    if len(opts) != 0:
        for o,a in opts:
            if o == "-f":
                needLoad = True

    import cPickle as pkl
    sys.path.extend(["./fw2"])
    import nCache
    sys.path.pop()
    import nCacheHooker as ch
    import GraphBuilder as gb
    import metis_graph as mg
    import os
    import common_tools as ctools
    from common_tools import setReadOnly
    from local_para import *

    oldenv = os.path.abspath('.')
    os.chdir(dumpFilePath)
    fileName = mxcFile

    if not needLoad:
        # step 1
        logger = ctools.getDefaultLogger(ctools.renameWithBase("log.log"))
        logger.info("start to build graph.")
        logger.info(reportSettings())

        builder = ch.GraphBuildHooker(radius)
        builder.startLoop("Build InitGraph:")
        nCache.loop(fileName, builder, nFrame)
        builder.endLoop()

        nStrand, nParticle, edges, refFrame = builder.graph()
        factor = nParticle/nStrand

        thresh = nFrame * frameFilter
        gb.filterEdges(edges, thresh)

        refFrame.calcParticleDirections()
        ruler = ch.ConnectionCalcHooker(edges, refFrame)
        ruler.startLoop("Measure the deviation:")
        nCache.loop(fileName, ruler, nFrame)
        ruler.endLoop()

        pkl.dump(edges, file('edges.dump', 'w'))
        setReadOnly('edges.dump')

        #step 2
        strandGraph = gb.shrinkGraph(edges, factor)

        particleGraph = mg.MetisGraph(edges, nParticle)
        strandGraph = mg.MetisGraph(strandGraph, nStrand)
        gb.normalize(particleGraph, nStep)
        gb.normalize(strandGraph, nStep)

        pkl.dump(particleGraph, file('mgA.dump', 'w'))
        setReadOnly('mgA.dump')
        pkl.dump(strandGraph, file('mgB.dump', 'w'))
        setReadOnly('mgB.dump')

        pkl.dump((nStrand, nParticle, factor, refFrame, radius, frameFilter),\
         file('info.dump', 'w'))

        logger.info("end to build graph.")

    else:
        nStrand, nParticle, factor, refFrame, radius, frameFilter = pkl.load(file('info.dump', 'r'))
        strandGraph = pkl.load(file('mgB.dump'))
        refFrame.calcParticleDirections()
        # step 3
        _g = strandGraph

        import networkx as nx
        # import metis
        import metis_graph as mg
        # G = nx.Graph()
        # G.add_nodes_from(range(nStrand))
        # itr = mg.UndirectedIterator(_g)
        # for edge in itr:
        #     G.add_edge(edge[0], edge[1], weight=edge[2])

        # cut, vers = metis.part_graph(G, nGroup)
        import pymetis
        cut, vers = pymetis.part_graph(nGroup, xadj=_g.xadj, adjncy=_g.adjncy, eweights=_g.eweights)

        f = open(str(nGroup)+".group","wb")
        import struct
        f.write(struct.pack('i', len(vers)))
        for i in vers:
            f.write(struct.pack('i', i))
        f.close()

        # rand, opt, worst
        prefix = ("None",)

        for opt in guideOpts:

            import guide_hair as gh
            starttime = time.strftime('%Y-%m-%d  %Hh%Mm%Ss',time.localtime(time.time()))
            hairGroup = gh.GroupedGraph(strandGraph, vers)
            hairGroup.solve(opt)
            sign = opt+'-'
            sign += time.strftime('%m-%d %Hh%Mm%Ss',time.localtime(time.time()))
            hairGroup.dumpNeighbourMap(prefix[0])

            guideImporter = ch.GuideHairHooker(hairGroup.guide, refFrame)
            guideImporter.startLoop("Import guide hair data with %d frames:" % nFrame)
            nCache.loop(fileName, guideImporter, nFrame)
            guideImporter.endLoop()

            guideData = guideImporter.getResult()
            guideExportFileName = sign+".guide"
            guideImporter.export(guideExportFileName, factor)
            setReadOnly(guideExportFileName)

            error0 = 0.0
            error = 0.0
            weights = []
            if nStrand % split == 0:
                nTotal = split
            else:
                nTotal = split + 1
            for i in range(nTotal):
                nImporter = ch.NormalHairHooker(guideData, refFrame, i, split, hairGroup)
                nImporter.startLoop("precomputation %d / %d:" % (i+1, split))
                nCache.loop(fileName, nImporter, nFrame)
                nImporter.endLoop()
                w, e0, e = nImporter.getResult()
                weights += w
                error0 += e0
                error += e

            pkl.dump((hairGroup.guide, weights), file(sign+"-weights.dump", 'wb'), 2)
            setReadOnly(sign+"-weights.dump")

            print "Total: error decrease from %f to %f." % (error0, error)

            endtime = time.strftime('%m-%d  %Hh%Mm%Ss',time.localtime(time.time()))
            print "end at:", endtime

            # generate the report
            if bReport:
                from sendMail import *
                content = 'Processing from '+starttime+' to '+endtime+'\n'
                content += 'Weight discretization: %d\n' % nStep
                content += 'Group number: %d\n' % nGroup
                content += 'Radius : %f\n' % radius
                content += 'Frame filter: %f\n' % frameFilter
                content += 'Prefix: %s\n' % prefix[0]
                content += 'Signature: %s\n' % sign
                content += 'Guide selection: %s\n' % opt
                content += 'Frame number: %d\n' % nFrame
                content += 'Guide sum %f, energy from %f to %f\n' % (hairGroup.energy, error0, error)
                content += 'Guide hair selection:\n'
                content += repr(hairGroup.guide)

                print content

                f = open("../Report/"+sign+".txt", 'w');
                f.write(content)
                f.close()

                if bMail:
                    send_mail(mailto_list, 'Report in 30/March '+sign+'-'+prefix[0], content)
