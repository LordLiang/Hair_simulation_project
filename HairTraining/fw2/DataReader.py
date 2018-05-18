from common_tools import *
from coordinates import *
import array
import numpy as np

class FrameData:
    def __init__(self):
        self.headMotion = None
        self.position = None
        self.direction = None

class HairHeader:
    def __init__(self):
        self.nParticle = None
        self.nHair = None
        self.factor = None

class HairDataReader:
    def __init__(self, fileName, args=None):
        if args is None:
            args = {'type':'anim2'}

        self.type = tryGetPara(args, "type")
        if type(self.type) == str and self.type[0] == '.':
            self.type = self.type[1:]

        if self.type == "anim2":
            self.file = open(fileName, 'rb')
            self.nFrame = readInt(self.file)
            self.nParticle = readInt(self.file)
            self.start = self.file.tell()
            self.offset = 4* (1+16 + 6*self.nParticle)
            self.ptrPos = None
            self.rewind()
            self.bbox = None

            # get the offset for some frame start from 1
            tmp = self.file.tell()
            self.ptrOffset = readInt(self.file)
            self.file.seek(tmp)

            self.boundingbox()

    def boundingbox(self):
        tmp = self.ptrPos
        self.rewind()
        frame = self.getNextFrame()
        bbox = None
        if self.type == "anim2":
            pos = np.array(frame.position)
            pos.shape = -1, 3
            bbox = []
            for i in range(3):
                bbox.append(min(pos[:,i]))
                bbox.append(max(pos[:,i]))

        self.seek(tmp)
        self.bbox = BoundingBox(bbox)

    def rewind(self):
        if self.type == "anim2":
            self.file.seek(self.start)
        self.ptrPos = 0

    def getNextFrameNoRewind(self):
        if self.ptrPos >= self.nFrame:
            return None

        res = None
        if self.type == "anim2":
            res = self._nextframeAnim2()

        self.ptrPos += 1
        return res


    def _nextframeAnim2(self):
        frameIdInFile = readInt(self.file)
        assert self.ptrPos == frameIdInFile - self.ptrOffset
        frame = FrameData()

        tmp = array.array('f')
        tmp.fromfile(self.file, 16)
        frame.headMotion = MatrixToRt(np.matrix(tmp).reshape((4, 4)))

        frame.position = array.array('f')
        frame.position.fromfile(self.file, self.nParticle * 3)

        frame.direction = array.array('f')
        frame.direction.fromfile(self.file, self.nParticle * 3)

        return frame

    def getNextFrame(self):
        if self.ptrPos >= self.nFrame:
            self.rewind()

        res = None
        if self.type == "anim2":
            res = self._nextframeAnim2()

        self.ptrPos += 1
        return res


    def randomGetFrame(self, n):
        self.seek(n)
        self.getNextFrame()

    def seek(self, n):
        if self.type == "anim2":
            tmp = self.start + self.offset * n
            self.file.seek(tmp)
        self.ptrPos = n

    def close(self):
        self.file.close()


if __name__== "__main__":
    fileName = r"D:\Data\20kcurly\anim1.anim2"
    a = HairDataReader(fileName)
    print a.bbox
