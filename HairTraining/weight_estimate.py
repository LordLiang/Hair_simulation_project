from scipy.optimize import minimize
import coordinates as cd
import numpy as np
import cPickle as pkl
from progressbar import *

npar = 25 # particle per strand

class SkinModel:

    def __init__(self, ref, guideData, frames, graph, task):
        self.nFrame = len(frames)
        self.weights0 = [None] * frames[0].n_hair
        self.weights = [None] * frames[0].n_hair
        self.data = frames
        self.graph = graph
        self.guide = guideData
        self.refFrame = ref
        self.task = task
        self.offset = task[0]

        for i in range(frames[0].n_hair):
            self.weights0[i] = [None, None]
            self.weights[i] = [None, None]

    def collectCi(self, s):
        ti = self.graph.hairGroup[s]
        return self.graph.groupGuideMap[ti]

    def reCollectCi(self, s):
        if len(self.weights0[s][0]) < 10:
            return self.weights0[s][1]

        rank = zip(self.weights0[s][0], self.weights0[s][1])
        rank.sort(key=lambda x:x[0], reverse=True)
        Ci = []
        for i in range(10):
            Ci.append(rank[i][1])
        return Ci

    def solve(self):
        self.estimate(self.collectCi)
        self.weights0, self.weights = self.weights, self.weights0
        self.estimate(self.reCollectCi)

    def estimate(self, findGuide):
        print "estimating weights..."
        self.error = 0.0
        self.error0 = 0.0
        pbar = ProgressBar().start()
        count = 0
        for i in self.task:
            count += 1
            if self.graph.isGuideHair(i):
                continue

            Ci = findGuide(i)
            nw = len(Ci)
            cons = ({'type': 'eq',
                     'fun' : lambda x: np.sum(x)-1.0,
                     'jac' : lambda x: np.ones(len(x))
                     },
                     {'type': 'ineq',
                      'fun' : lambda x: x,
                      'jac' : lambda x: np.identity(len(x))
                      })

            res = minimize(SkinModel.evalError, [1.0/nw]*nw, args=(self, i, Ci),
             jac=SkinModel.evalDerive, options={'disp': False}, method='SLSQP', constraints=cons)

            map(lambda x: 0 if (x < 0.0) else x, res.x)
            self.weights[i][0] = res.x
            self.weights[i][1] = Ci
            pbar.update(100*(count)/(len(self.task)))

            error0 = SkinModel.evalError([1.0/nw]*nw, self, i, Ci)
            error = SkinModel.evalError(self.weights[i][0], self, i, Ci)

            self.error0 += error0
            self.error += error

        pbar.finish()
        print "error decrease from %f to %f." % (self.error0, self.error)

    @staticmethod
    def evalError(x, inst, s, Ci, idx = [-1]):
        if idx[0] != s:
            t0 = inst.refFrame.data[s*npar:(s+1)*npar], inst.refFrame.particle_direction[s*npar:(s+1)*npar]
            n = len(x)
            sumAAT = np.matrix(np.zeros((n, n)))
            sumAs = np.matrix(np.zeros(n))
            sumSST = 0.0

            for fn in range(inst.nFrame):
                A = []
                frame = inst.data[fn]
                guide = inst.guide[fn]
                tref = cd.rigid_trans_batch(frame.rigid_motion, t0)

                s2 = s - inst.offset
                treal = np.array([frame.data[s2*npar:(s2+1)*npar], frame.particle_direction[s2*npar:(s2+1)*npar]])
                treal.resize(6*npar)
                for g in Ci:
                    Bg = guide.particle_motions[g]
                    state = np.array(cd.point_trans_batch(Bg, tref))
                    state.resize(6*npar)
                    A.append(state)
                A = np.matrix(A)
                sumAAT += A*A.T
                sumAs += np.matrix(treal)*A.T
                sumSST += treal.dot(treal)
            inst.cacheMatrices(sumAAT, sumAs, sumSST);
            idx[0] = s
        else:
            sumAAT, sumAs, sumSST = inst.retrieveMatrices()

        return (x * sumAAT).dot(x) - 2 * sumAs.dot(x) + sumSST

    @staticmethod
    def evalDerive(x, inst, s, Ci):
        AAT, As, SST = inst.retrieveMatrices()
        return (2 * AAT.dot(x) - 2 * As).A1

    def cacheMatrices(self, AAT, As, SST):
        self.AAT = AAT
        self.As = As
        self.SST = SST

    def retrieveMatrices(self):
        return self.AAT, self.As, self.SST

    def getResult(self):
        return self.weights

    def dump(self, f):
        pkl.dump(self.weights, f, 2)

    def load(self, f):
        self.weights = pkl.load(f)
