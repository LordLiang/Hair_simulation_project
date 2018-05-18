import numpy as np
from coordinates import *
import cPickle as pkl

n_particle_per_strand = 25

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

    def check(self):
        return self.data and self.n_hair and self.headData

    def loadIntoMemory(self, name, sz, data):
        import re
        vertexCounts = re.compile(".*vertexcounts.*", re.I)
        hairCounts = re.compile(".*haircounts.*", re.I)
        vertexPositions = re.compile(".*positions.*", re.I)
        headVertex = re.compile(".*rigid.*", re.I)

        if (headVertex.match(name)):
            self.n_headVertex = int(sz)
            self.headData = np.array(data).reshape((-1, 3))

        elif (hairCounts.match(name)):
            self.n_hair = int(data[0])
            self.n_particle = self.n_hair * n_particle_per_strand

        elif (vertexPositions.match(name)):
            self.data = np.array(data).reshape((-1, 3))
            tmp = self.data.reshape((self.n_hair, -1))
            self.headData2 = tmp[:, :3].reshape((-1, 3))

        self.count += 1

    def calcParticleMotionMatrices(self):
        ref = self.reference
        matrices = []
        for i in range(self.n_particle):
            refstate = rigid_trans_full(self.rigid_motion, (ref.data[i], ref.particle_direction[i]))
            trans = self.data[i] - refstate[0]
            rot = vector_rotation_3D(refstate[1], self.particle_direction[i])
            matrices.append((rot, trans))

        self.particle_motions = matrices

    def calcParticleDirections(self):
        from scipy import interpolate
        u_axis = np.linspace(0, 1, 25)

        directions = []
        for i in range(self.n_hair):
            begin = n_particle_per_strand*i
            end = n_particle_per_strand*(i+1)

            data = self.data[begin:end].T
            spline, u = interpolate.splprep(data, s=0)
            derive = interpolate.splev(u_axis, spline, der=1)

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
        self.calcParticleMotionMatrices()

    def calcRigidMotionMatrix(self, reference):
        self.reference = reference
        rigid = rigid_transform_3D(matrix(reference.headData2), matrix(self.headData2))
        self.rigid_motion = rigid
        import logging
        logging.debug(str(rigid))
        #print rigid
        self._calcRigid()

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
        self._calcRigid()

    def loadCache20(self, f):
        self.rigidMotionMatrix, self.rigid_motion, self.particle_direction = pkl.load(file(f, 'rb'))

    @staticmethod
    def importDirections(f):
        return pkl.load(file(f, 'rb'))[1]