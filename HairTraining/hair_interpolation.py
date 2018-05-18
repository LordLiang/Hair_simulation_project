from weight_estimate import npar
from struct import pack
import coordinates as cd
import numpy as np
import array

class HairInterpolation:

    def __init__(self, guideData, weights, reference, fileName):
        self.guideData = guideData
        self.weights = weights
        self.refFrame = reference
        self.fileName = fileName

        self.nFrame = len(guideData)
        self.nStrand = len(weights)

        print "frame %d, strand %d" % (self.nFrame, self.nStrand)

    def interpolate(self):
        f = open(self.fileName, 'wb')
        f.write(pack('i', self.nFrame))
        f.write(pack('i', self.nStrand*npar))

        bar = ProgressBar().start()
        for i in range(self.nFrame):
            bar.update(i*100/self.nFrame)
            f.write(pack('i', i))
            for j in range(self.nStrand):
                s = self.strandInterpolation(j, i)
                for k in range(npar*3):
                    f.write(pack('f', s[k]))
        bar.finish()
        f.close()

    def strandInterpolation(self, s, fn):
        if self.weights[s][0] == None:
            Ci = [s]
            w = 1.0
        else:
            Ci = self.weights[s][1]
            w = self.weights[s][0]

        t0 = self.refFrame.data[s*npar:(s+1)*npar]
        guide = self.guideData[fn]
        tref = cd.rigid_trans_batch_no_dir(guide.rigid_motion, t0)
        A = []
        for g in Ci:
            Bg = guide.particle_motions[g]
            state = np.array(cd.point_trans_batch_no_dir(Bg, tref))
            import ipdb; ipdb.set_trace()
            state.resize(3*npar)
            A.append(state)
        A = np.matrix(A)
        return (A.T * np.matrix(w).T).A1

class HairInterpolation20:

    def __init__(self, guideData, weights, reference, fileName):
        self.guideData = guideData
        self.weights = weights
        self.refFrame = reference
        self.fileName = fileName

        self.nFrame = len(guideData)
        self.nStrand = len(weights)

        print "frame %d, strand %d" % (self.nFrame, self.nStrand)

    # @profile
    def interpolate(self):
        f = open(self.fileName, 'wb')
        f.write(pack('i', self.nFrame))
        f.write(pack('i', self.nStrand*npar))

        bar = ProgressBar().start()
        for i in range(self.nFrame):
            bar.update(i*100/self.nFrame)
            f.write(pack('i', i))
            for i1 in range(4):
                for j in range(4):
                    f.write(pack('f', self.guideData[i].rigidMotionMatrix[i1, j]))

            poss = np.empty(self.nStrand*npar*3)
            dirs = np.empty(self.nStrand*npar*3)
            for j in range(self.nStrand):
                s = self.strandInterpolation(j, i)
                poss[j*npar*3:(j+1)*npar*3] = s[:npar*3]
                dirs[j*npar*3:(j+1)*npar*3] = s[npar*3:]
                # import ipdb; ipdb.set_trace()

            array.array('f', poss).tofile(f)
            array.array('f', dirs).tofile(f)

        bar.finish()
        f.close()

    # @profile
    def strandInterpolation(self, s, fn):
        if self.weights[s][0] == None:
            Ci = [s]
            w = 1.0
        else:
            Ci = self.weights[s][1]
            w = self.weights[s][0]

        s0 = (self.refFrame.data[s*npar:(s+1)*npar], self.refFrame.particle_direction[s*npar:(s+1)*npar])
        guide = self.guideData[fn]
        tref = cd.rigid_trans_batch(guide.rigid_motion, s0)
        A = []
        for g in Ci:
            Bg = guide.particle_motions[g]
            state = np.array(cd.point_trans_batch(Bg, tref))
            state.resize(6*npar)
            A.append(state)
        A = np.matrix(A)
        return (A.T * np.matrix(w).T).A1

if __name__ == "__main__":
    import cPickle as pkl
    import nCacheHooker as ch

    import nCache
    from progressbar import*
    import crash_on_ipy
    from local_para import *
    import os
    os.chdir(dumpFilePath)

    nFrame = 200
    # fileName = "../../maya cache/03074/hair_nRigidShape1.xml"
    fileName = mxcFile

    nStrand, nParticle, factor, refFrame, radius, frameFilter = pkl.load(file(dumpFilePath+'\info.dump', 'r'))
    guide, weights = pkl.load(file(wFile, 'rb'))
    factor = 5

    n = len(weights)
    # print len(weights)
    # if n != 4245:
    #     nStrand = n/factor
    #     for i in range(n/factor):
    #         for j in range(1, factor):
    #             if weights[j*nStrand+i][0] != None:
    #                 weights[i] = weights[j*nStrand+i]
    #     weights = weights[:nStrand]
    # else:
    #     nStrand = n
    print len(weights)

    guideImporter = ch.GuideHairHooker(guide, refFrame)
    guideImporter.startLoop("Import guide hair data with %d frames:" % nFrame)
    nCache.loop(fileName, guideImporter, nFrame)
    guideImporter.endLoop()

    guideData = guideImporter.getResult()

    cache = HairInterpolation20(guideData, weights, refFrame, cacheFile)
    cache.interpolate()
