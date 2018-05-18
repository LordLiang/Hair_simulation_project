import nCache
import nCacheHooker as ch
from pipeline import *
import struct
import array

import crash_on_ipy



class ConverterHooker(ch.Hooker):
    def __init__(self, fileName, needDirection=False):
        super(ConverterHooker, self).__init__()
        # self.file = open(fileName, 'w')
        self.fileb = open(fileName, 'wb')
        self.needDirection = needDirection

        # if not self.file or not self.fileb:
        if not self.fileb:
            raise Exception("File not open!")

    def postFrame(self):
        self.computeRigidMotionAndDirection();
        if self.i == 0:
            # self.file.write(str(self.nFrame))
            # self.file.write("\n")
            # self.file.write(str(self.frame.n_particle))
            # self.file.write("\n")

            self.fileb.write(struct.pack('i', self.nFrame))
            self.fileb.write(struct.pack('i', self.frame.n_particle))

        # self.file.write("Frame %d\n" % self.i)
        self.fileb.write(struct.pack('i', self.i))

        # for pos in self.frame.data:
        #     self.file.write("%f %f %f\n" % (pos[0], pos[1], pos[2]))

        for i in range(4):
            for j in range(4):
                self.fileb.write(struct.pack('f', self.frame.rigidMotionMatrix[i, j]))

        self.data.tofile(self.fileb)
        if self.needDirection:
            array.array('f', self.frame.particle_direction.flatten()).tofile(self.fileb)
        super(ConverterHooker, self).postFrame()

    def endLoop(self):
        # self.file.close()
        self.fileb.close()
        super(ConverterHooker, self).endLoop()

    def dataHooker(self, name, sz, arr):
        import re
        expr = re.compile(".*positions.*", re.I)
        if (expr.match(name)):
            self.data = arr
        super(ConverterHooker, self).dataHooker(name, sz, arr)

    def computeRigidMotionAndDirection(self):
        if self.i == 0:
            self.reference = self.frame

        self.frame.calcRigidMotionMatrix(self.reference)
        if self.needDirection:
            self.frame.calcParticleDirections()


if __name__ == "__main__":
    import sys

    conv = ConverterHooker(sys.argv[2], True)
    conv.startLoop("Convert to anim file:")
    nCache.loop(sys.argv[1], conv, 200)
    conv.endLoop()
