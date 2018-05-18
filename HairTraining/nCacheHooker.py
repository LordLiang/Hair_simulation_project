from frame import Frame
from progressbar import *
from GraphBuilder import *
import numpy as np

class Hooker(object):
    def __init__(self, number=None):
        self.nFrame = number
        self.i = -1
        return

    def startLoop(self, title="start loop:"):
        print title

    def endLoop(self):
        pass

    def resetPass(self):
        self.i2 = -1

    def newFrame(self):
        if self.i < 0:
            print "Reading on cache."
            self.bar =  ProgressBar().start()
        self.frame = Frame()
        self.i += 1
        self.i2 += 1
        return

    def postFrame(self):
        self.bar.update((self.i2+1)*100/self.nFrame)
        if self.i2 == self.nFrame-1:
            self.bar.finish()
        return

    def dataHooker(self, name, sz, arr):
        self.frame.loadIntoMemory(name, sz, arr)
        return

class GraphBuildHooker(Hooker):
    def __init__(self, radius):
        super(GraphBuildHooker, self).__init__()
        self.radius = radius
        self.edges = {}

    def postFrame(self):
        factor = self.frame.n_particle /  self.frame.n_hair
        self.edges = createInitGraphLoop(self.radius, self.frame,\
         self.edges, self.i, factor)
        if self.i == 0:
            self.refFrame = self.frame
            self.nParticle = self.frame.n_particle
            self.nStrand = self.frame.n_hair
            print "There are %d edges in the first frame" % len(self.edges)

        super(GraphBuildHooker, self).postFrame()

    def graph(self):
        return self.nStrand, self.nParticle, self.edges, self.refFrame

class ConnectionCalcHooker(Hooker):
    def __init__(self, edges, reference):
        super(ConnectionCalcHooker, self).__init__()
        self.edges = edges
        self.reference = reference
        for k in edges.keys():
            edges[k] = np.zeros(2)
        import os
        self.path = "frame/"
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def postFrame(self):
        self.frame.calcParticleDirections()
        self.frame.calcMotionMatrix(self.reference)
        self.frame.cacheInfo(self.path+"frame"+str(self.i)+".dump")
        for k in self.edges.keys():
            self.edges[k] -= np.array(self.frame.deviationVector(k[0], k[1]))
        super(ConnectionCalcHooker, self).postFrame()

    def endLoop(self):
        c0 = 0.0
        c1 = 0.0
        for val in self.edges.values():
            c0 += val[0]
            c1 += val[1]

        coef = c0 / c1
        for k in self.edges.keys():
            self.edges[k] = self.edges[k][0] + self.edges[k][1] * coef

        super(ConnectionCalcHooker, self).endLoop()
        print "Coefficients are %f, %f." % (c0, c1)



class GuideHairHooker(Hooker):
    def __init__(self, guide, ref):
        super(GuideHairHooker, self).__init__()
        self.data = []
        self.guide = guide
        self.refFrame = ref

    def postFrame(self):
        dumpFile = "frame/frame"+str(self.i)+".dump"
        self.frame.selectGuideHair(self.guide, dumpFile)
        self.frame.calcSelectedParticleMotionMatrices(self.refFrame, self.guide)
        self.frame.clearAsGuideInfo()
        self.data.append(self.frame)
        super(GuideHairHooker, self).postFrame()

    def getResult(self):
        return self.data

    def export(self, fileName, factor):
        f = open(fileName, "wb")
        import struct
        f.write(struct.pack('i', len(self.guide)))
        f.write(struct.pack('i', factor))
        f.write(struct.pack('i', self.nFrame))

        for idx in self.guide:
            f.write(struct.pack('i', idx))

        for i in range(self.nFrame):
            f.write(struct.pack('i', i))
            for idx in self.guide:
                trans = self.data[i].particle_motions[idx]
                for k in range(factor):
                    R, T = trans[k]
                    for a in range(3):
                        for b in range(3):
                            f.write(struct.pack('f', R[a, b]))
                    for a in range(3):
                        f.write(struct.pack('f', T[a]))

        f.close()
        return

class NormalHairHooker(Hooker):
    def __init__(self, guideData, ref, i, split, graph):
        super(NormalHairHooker, self).__init__()

        self.guide = guideData
        self.graph = graph
        self.refFrame = ref

        self.data = []

        nStrand = self.guide[0].n_hair
        step = nStrand / split

        self.start = i * step
        self.end = (i+1) * step
        if self.end >= nStrand:
            self.end = nStrand

    def postFrame(self):
        dumpFile = "frame/frame"+str(self.i)+".dump"
        self.frame.selectNormalHair(self.start, self.end, dumpFile)
        self.data.append(self.frame)
        super(NormalHairHooker, self).postFrame()

    def endLoop(self):
        super(NormalHairHooker, self).endLoop()
        import weight_estimate as wet
        model = wet.SkinModel(self.refFrame, self.guide, self.data, self.graph, range(self.start, self.end))
        model.solve()
        self.weights = model.weights[self.start:self.end]
        self.error0 = model.error0
        self.error = model.error

    def getResult(self):
        return self.weights, self.error0, self.error
