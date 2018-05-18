import numpy as np
from coordinates import *
import cPickle as pkl
from joblib.pool import has_shareable_memory

n_particle_per_strand = 25


def frame_work(rigid, refp, refd, cp, cd):
    refstate = rigid_trans_full(rigid, (refp, refd))
    trans = cp - refstate[0]
    rot = vector_rotation_3D(refd, cd)
    return (rot, trans)

class Frame:

    def __init__(self):
        self.count = 0
        self.data = None # 2D array
        self.headData = None # 2D array

        self.n_headVertex = 0
        self.n_hair = 0
        self.n_particle = 0

        self.rigid_motion = None # matrix R, array t
        self.particle_motions = None # list of (matrix R, array t)
        self.reference = None

        self.hairspline = []
        self.particle_direction = None  # 2D array

    def loadIntoMemory(self, name, sz, data):
        import re
        vertexCounts = re.compile(".*vertexcounts.*", re.I)
        hairCounts = re.compile(".*haircounts.*", re.I)
        vertexPositions = re.compile(".*positions.*", re.I)
        headVertex = re.compile(".*rigid.*", re.I)

        if (headVertex.match(name)):
        # if self.count == 0:
            # head data
            self.n_headVertex = int(sz)
            self.headData = np.array(data)
            self.headData.resize(len(data)/3, 3)

        elif (hairCounts.match(name)):
        # elif self.count == 1:
            self.n_hair = int(data[0])
            self.n_particle = self.n_hair * n_particle_per_strand

        elif (vertexPositions.match(name)):
        # elif self.count == 3:
            # hair data
            self.data = np.array(data)
            self.data.resize(self.n_particle, 3)

        self.count += 1

    def selectGuideHair(self, select, fileName):
        self.loadCache(fileName)
        data = {}
        dirs = {}
        for i in select:
            for j in range(n_particle_per_strand):
                ii = n_particle_per_strand * i + j
                data[ii] = self.data[ii]
                dirs[ii] = self.particle_direction[ii]
        self.data = data
        self.particle_direction = dirs

    def selectNormalHair(self, start, end, fileName):
        self.loadCache(fileName)
        self.data = self.data[start*n_particle_per_strand:\
            end*n_particle_per_strand]
        self.particle_direction = self.particle_direction[start*n_particle_per_strand:\
            end*n_particle_per_strand]
        del self.headData

    def calcParticleMotionMatrices(self):
        ref = self.reference
        matrices = []
        for i in range(self.n_particle):
            refstate = rigid_trans_full(self.rigid_motion, (ref.data[i], ref.particle_direction[i]))
            trans = self.data[i] - refstate[0]
            rot = vector_rotation_3D(refstate[1], self.particle_direction[i])
            matrices.append((rot, trans))

        self.particle_motions = matrices

    def calcParticleMotionMatrices_parallel(self):
        ref = self.reference
        self.particle_motions = Parallel(n_jobs=4, max_nbytes=1e6)(delayed(frame_work)\
            (self.rigid_motion, ref.data[i], ref.particle_direction[i], self.data[i], self.particle_direction[i])\
             for i in range(self.n_particle))

    def calcSelectedParticleMotionMatrices(self, reference, Ids):
        ref = reference
        self.reference = ref
        matrices = {}
        for i in Ids:
            transes = []
            for j in range(n_particle_per_strand):
                ii = n_particle_per_strand * i + j
                refstate = rigid_trans_full(self.rigid_motion, (ref.data[ii], ref.particle_direction[ii]))
                trans = self.data[ii] - refstate[0]
                rot = vector_rotation_3D(refstate[1], self.particle_direction[ii])
                transes.append((rot, trans))
            matrices[i] = transes

        self.particle_motions = matrices

    def calcParticleDirections(self):
        from scipy import interpolate
        u_axis = np.linspace(0, 1, 25)

        directions = []
        for i in range(self.n_hair):
            begin = n_particle_per_strand*i
            end = n_particle_per_strand*(i+1)

            data = self.data[begin:end].T
            spline, u = interpolate.splprep(data, s=0) #Find the B-spline representation of an N-dimensional curve.
            derive = interpolate.splev(u_axis, spline, der=1) #Evaluate a B-spline or its derivatives

            derive = np.matrix(derive).T
            for j in range(n_particle_per_strand):
                directions.append(derive[j] / np.linalg.norm(derive[j]))
            self.hairspline.append(spline)

        self.particle_direction = np.array(directions)
        self.particle_direction.resize(self.n_particle, 3)

    def deviation(self, id0, id1):

        cur0 = self.data[id0], self.particle_direction[id0]
        cur1 = self.data[id1], self.particle_direction[id1]

        t0 = self.particle_motions[id0]
        t1 = self.particle_motions[id1]
        t = self.rigid_motion

        ref0 = rigid_trans_full(t, (self.reference.data[id0],
            self.reference.particle_direction[id0]))
        ref1 = rigid_trans_full(t, (self.reference.data[id1],
            self.reference.particle_direction[id1]))

        return squared_diff(point_trans(t0, ref1), cur1) + \
            squared_diff(point_trans(t1, ref0), cur0)

    def deviationVector(self, id0, id1):

        cur0 = self.data[id0], self.particle_direction[id0]
        cur1 = self.data[id1], self.particle_direction[id1]

        t0 = self.particle_motions[id0]
        t1 = self.particle_motions[id1]
        t = self.rigid_motion

        ref0 = rigid_trans_full(t, (self.reference.data[id0],
            self.reference.particle_direction[id0]))
        ref1 = rigid_trans_full(t, (self.reference.data[id1],
            self.reference.particle_direction[id1]))

        return squared_diff(point_trans(t0, ref1), cur1),\
            squared_diff(point_trans(t1, ref0), cur0)


    def calcMotionMatrix(self, reference):
        self.reference = reference
        self.calcRigidMotionMatrix(reference)
        self.calcParticleMotionMatrices();

    def calcRigidMotionMatrix(self, reference):
        self.reference = reference
        rigid = rigid_transform_3D(matrix(reference.headData), matrix(self.headData))
        self.rigid_motion = rigid
        self._calcRigid();

    def _calcRigid(self):
        rigid = self.rigid_motion
        trans3x4 = np.vstack([rigid[0].T, rigid[1]]).T
        self.rigidMotionMatrix = np.matrix(np.vstack([trans3x4, np.array([0,0,0,1])]))

    def clearMotionMatrix(self):
        del self.particle_motions
        del self.rigid_motion
        del self.particle_direction
        del self.hairspline

    def cacheInfo(self, f):
        pkl.dump((self.rigid_motion, self.particle_direction), file(f, 'wb'), 2)

    def cacheInfo20(self, f):
        pkl.dump((self.rigidMotionMatrix, self.rigid_motion, self.particle_direction), file(f, 'wb'), 2)

    def loadCache(self, f):
        self.rigid_motion, self.particle_direction = pkl.load(file(f, 'rb'))
        self._calcRigid();

    def loadCache20(self, f):
        self.rigidMotionMatrix, self.rigid_motion, self.particle_direction = pkl.load(file(f, 'rb'))

    def importDirections(self, f):
        return pkl.load(file(f, 'rb'))[1]

    def clearAsGuideInfo(self):
        del self.data
        del self.particle_direction
        del self.headData
