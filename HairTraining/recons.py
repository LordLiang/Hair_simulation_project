from local_para_small import ReconsPara, dumpFilePath
import cPickle as pkl
from common_tools import *

class ReconsturctionData:

    def __init__(self):
        # input list
        self.file_reference = None
        self.file_guide = None
        self.file_interpolation = None
        self.file_group = None
        self.file_neigh = None

        self.dump_info = None
        self.dump_weights = None

        self.sectionFlag = 0b000
        self.maskGroup = 0b001
        self.maskNeigh = 0b010
        self.maskIntpl = 0b100

        # head
        self.n_particle = None
        self.n_strand = None
        self.factor = None

        # head2
        self.n_group = None
        self.n_frame = None
        self.mcx = None

        # index section
        self.idx_guide = 0
        self.idx_frame = 0
        self.idx_weights = 0
        self.idx_group = 0
        self.idx_neigh = 0
        self.idx_intpl = 0

        # guide section
        self.guideId = None # array

        # group section
        self.particleGroupId = None # array

        # intpl section
        self.anim2Path = None

    def computeIndices(self):
        idxTmp = 0

        self.idx_guide = idxTmp + 12+128+12+12
        idxTmp = self.idx_guide

        self.idx_frame = idxTmp + 4*self.n_group + \
            24 * self.n_group * self.factor + \
            self.n_frame * (4+64+48*self.n_group*self.factor)
        idxTmp = self.idx_frame

        self.idx_weights = idxTmp + 24 * self.n_particle
        idxTmp = self.idx_weights

        self.idx_group = 0
        self.idx_neigh = 0
        self.idx_intpl = 0

        if self.sectionFlag & self.maskGroup:
            nWeights = self.n_group + self.weightsSectionLength()
            self.idx_group = idxTmp+4+4*self.n_strand+8*nWeights
            idxTmp = self.idx_group

        if self.sectionFlag & self.maskNeigh:
            if self.sectionFlag & self.maskGroup:
                idxTmp += 4 * self.n_strand
            self.idx_neigh = idxTmp

        import os
        if self.sectionFlag & self.maskIntpl:
            if self.sectionFlag & self.maskNeigh:
                idxTmp += os.path.getsize(self.file_neigh)-4
            self.idx_intpl = idxTmp

    @staticmethod
    def length(l):
        import numpy
        if type(l) != numpy.ndarray:
            return 0
        else: return l.size

    def weightsSectionLength(self):
        if not hasattr(self, 'weightLength') or self.weightLength == None:
            self.weightLength = sum(map(lambda x: ReconsturctionData.length(x[0]),\
                                  self.dump_weights[1]))
        return self.weightLength

if __name__ == "__main__":

    import sys
    import array

    import os
    os.chdir(dumpFilePath)
    exportName = sys.argv[1]
    assert(exportName != "")

    paras = ReconsPara()
    data = ReconsturctionData()

    data.dump_info = pkl.load(open(paras.info))
    data.dump_weights = pkl.load(open(paras.weights, 'rb'))

    data.sectionFlag = paras.flag

    data.file_reference = paras.reference
    data.file_guide = paras.guide

    if data.sectionFlag & data.maskGroup:
        data.file_group = paras.group

    if data.sectionFlag & data.maskNeigh:
        data.file_neigh = paras.neigh

    if data.sectionFlag & data.maskIntpl:
        data.file_interpolation = paras.interpolation

    data.n_particle = data.dump_info[1]
    data.n_strand =  data.dump_info[0]
    data.factor =  data.dump_info[2]

    data.n_group = len(data.dump_weights[0])
    with open(data.file_reference, 'rb') as f:
        data.n_frame = readInt(f)
    data.mcx = paras.mcx

    data.computeIndices()

    with open(data.file_guide, 'rb') as f:
        f.read(12)
        data.guideId = array.array('i')
        data.guideId.fromfile(f, data.n_group)

    if data.sectionFlag & data.maskGroup:
        with open(data.file_group, 'rb') as f:
            f.read(4)
            arr = array.array('i')
            arr.fromfile(f, data.n_strand)
            data.particleGroupId = arr

    if data.sectionFlag & data.maskIntpl:
        data.anim2Path = paras.interpolation


    with open(exportName, 'wb') as out:
        # head
        writeInt(out, data.n_particle)  # particle
        writeInt(out, data.n_strand)  # strand
        writeInt(out, data.factor)  # factor

        # head2
        writeInt(out, data.n_group)
        writeInt(out, data.n_frame)
        out.write(data.mcx)
        length = 140-out.tell()
        out.write('\0'*length)

        # index
        markIndex = out.tell()
        writeInt(out, data.idx_guide)
        writeInt(out, data.idx_frame)
        writeInt(out, data.idx_weights)
        writeInt(out, data.idx_group)
        writeInt(out, data.idx_neigh)
        writeInt(out, data.idx_intpl)

        # guide section
        assert(data.idx_guide == out.tell())
        data.guideId.tofile(out)
        reference = data.dump_info[3]

        for guideHair in data.guideId:
            tmp = guideHair * data.factor
            tmparr = array.array('f', reference.data[tmp:tmp+data.factor].flatten())
            tmparr.tofile(out)

        for guideHair in data.guideId:
            tmp = guideHair * data.factor
            tmparr = array.array('f', reference.particle_direction\
                [tmp:tmp+data.factor].flatten())
            tmparr.tofile(out)

        # guide section motion matrtix
        with open(data.file_reference, 'rb') as reffile:
            guidefile = open(data.file_guide, 'rb')
            strideGuide = 4+4*data.factor*data.n_group*12
            posGuide = 0
            offsetGuide = 3*4+4*data.n_group

            strideAnim = 4+16*4+2*3*4*data.n_particle
            posAnim = 0
            offsetAnim = 4
            for i in range(data.n_frame):
                writeInt(out, i)

                tmparr = array.array('f')
                reffile.seek(offsetAnim+i*strideAnim+8)
                tmparr.fromfile(reffile, 16)
                tmparr.tofile(out)

                guidefile.seek(offsetGuide + i * strideGuide + 4)
                tmparr = array.array('f')
                tmparr.fromfile(guidefile, data.factor*data.n_group*12)
                tmparr.tofile(out)

            guidefile.close()

        # initial frame section
        assert(data.idx_frame == out.tell())
        with open(data.file_reference, 'rb') as reffile:
            reffile.seek(19*4)
            tmparr = array.array('f')
            tmparr.fromfile(reffile, 6*data.n_particle)
            tmparr.tofile(out)

        # weight section
        assert(data.idx_weights == out.tell())
        writeInt(out, data.weightsSectionLength())
        for i in range(data.n_strand):
            weight = data.dump_weights[1][i]
            if type(weight[0]) == type(None):
                writeInt(out, 1)
                writeInt(out, i)
                writeFloat(out, 1.0)
            else:
                writeInt(out, weight[0].size)
                array.array('i', weight[1]).tofile(out)
                array.array('f', weight[0].tolist()).tofile(out)

        # group section
        if data.sectionFlag & data.maskGroup:
            assert(data.idx_group == out.tell())
            with open(data.file_group, 'rb') as f:
                f.seek(4)
                tmparr = array.array('i')
                tmparr.fromfile(f, data.n_strand)
                tmparr.tofile(out)

        # neighboring section
        if data.sectionFlag & data.maskNeigh:
            assert(data.idx_neigh == out.tell())
            with open(data.file_neigh, 'rb') as f:
                f.seek(4)
                while True:
                    buff = f.read(128)
                    if not buff:
                        break
                    out.write(buff)

        # interpolation section
        if data.sectionFlag & data.maskIntpl:
            assert(data.idx_intpl == out.tell())
            out.write(data.file_interpolation)
