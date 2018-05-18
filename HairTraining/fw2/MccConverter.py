import nCache
import struct, array
from progressbar import ProgressBar
from frame import Frame
from common_tools import *
import DataReader as DR


import crash_on_ipy

class nCacheHooker(object):
    def __init__(self, number=None):
        self.nFrame = number
        self.i = -1

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

    def postFrame(self):
        self.bar.update((self.i2+1)*100/self.nFrame)
        if self.i2 == self.nFrame-1:
            self.bar.finish()

    def dataHooker(self, name, sz, arr):
        self.frame.loadIntoMemory(name, sz, arr)

class ConverterHooker(nCacheHooker):
    def __init__(self, fileName, needDirection=False):
        super(ConverterHooker, self).__init__(None)
        self.fileb = open(fileName, 'wb')
        self.needDirection = needDirection

        if not self.fileb:
            raise Exception("File not open!")

    def postFrame(self):
        self.computeRigidMotionAndDirection()
        if self.i == 0:

            self.fileb.write(struct.pack('i', self.nFrame))
            self.fileb.write(struct.pack('i', self.frame.n_particle))

        self.fileb.write(struct.pack('i', self.i))

        for i in range(4):
            for j in range(4):
                self.fileb.write(struct.pack('f', self.frame.rigidMotionMatrix[i, j]))

        self.data.tofile(self.fileb)
        if self.needDirection:
            array.array('f', self.frame.particle_direction.flatten()).tofile(self.fileb)
        super(ConverterHooker, self).postFrame()

    def endLoop(self):
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


def mergeAnim2(fileList, target):

    postfix = ".anim2"
    nlast = len(postfix)
    for f in fileList:
        assert(f[-nlast:] == postfix)

    t = open(target, 'wb')
    oldHair = None
    frameId = 0
    for f in fileList:
        cur = DR.HairDataReader(f, {'type':postfix})
        if oldHair:
            assert cur.nParticle == oldHair

        if frameId == 0: # first file need header
            t.write(struct.pack('i', -1))
            t.write(struct.pack('i', cur.nParticle))

        for i in range(cur.nFrame):
            buffer = cur.file.read(cur.offset)
            assert buffer != '' and len(buffer) == cur.offset
            t.write(buffer)
            tmp = t.tell()
            t.seek(tmp-cur.offset)
            writeInt(t, frameId)
            t.seek(tmp)
            frameId += 1

        oldHair = cur.nParticle

    t.seek(0)
    writeInt(t, frameId)
    t.close()

    defaultLogInfo("Number of frames in total: %d" % frameId)


def mergeAllAnim2(path, target):
    import os
    old = os.path.abspath('.')
    os.chdir(path)

    fs = os.listdir('.')

    import re
    pattern = re.compile(r'.*\.anim2')

    fs = filter(lambda f: pattern.match(f) and f != target, fs)
    defaultLogInfo("All files: " + ','.join(fs))

    mergeAnim2(fs, target)
    os.chdir(old)

def mccOneFileToAnim2(fileName, target, nFrame):
    conv = ConverterHooker(target, True)
    conv.startLoop("Convert to anim file:")
    nCache.loop(fileName, conv, nFrame)
    conv.endLoop()

def mccPerFrameToAnim2(fileName, target):

    # import os, re
    # fileName = os.path.abspath(fileName)
    # dirName = os.path.dirname(fileName)
    #
    # baseName = os.path.basename(fileName).split('.')[0]
    # allFiles = os.listdir(dirName)
    # ids = []
    # matcher = re.compile(baseName)
    # nFrame = 0
    # for afile in allFiles:
    #     parts = os.path.splitext(afile)
    #     if (parts[1] == ".mcx" or parts[1] == ".mc") and matcher.match(afile) != None:
    #         id = eval(parts[0][len(baseName) + len('Frame'):])
    #         ids.append(id)
    #         nFrame += 1
    #
    # assert(nFrame == (max(ids)-min(ids)+1))
    #
    # defaultLogInfo("Found ncache %d files!" % nFrame)

    conv = ConverterHooker(target, True)
    conv.startLoop("Convert to anim file:")
    nCache.loop(fileName, conv)
    conv.endLoop()


if __name__ == "__main__":
    import sys

    # cmdLoggingDisp()
    setupDefaultLogger("D:/log/log2.log")

    # conv = ConverterHooker(sys.argv[2], True)
    # conv.startLoop("Convert to anim file:")
    # nCache.loop(sys.argv[1], conv, 200)
    # conv.endLoop()

    outputPath = r"D:\Data\20kcurly2"
    inputPath = r"D:\Data\modelimport\cache\curly20k\anim"

    for i in range(6):
        id = str(i+1)
        mccPerFrameToAnim2(inputPath+id+r"\anim"+id+".xml", outputPath+r"\anim"+id+".anim2")


    # mccPerFrameToAnim2(sys.argv[1], sys.argv[2])

    args= [r"D:\Data", "t.anim2"]
    mergeAllAnim2(outputPath, "total.anim2")

    nFrame = 500
    fileName = r"D:\Data\20kcurly2\total.anim2"


    # X, hairHeader, Data = SCGetMatrixAndHeader(fileName, nFrame)  # X: len(u_s) x nHair

    import guidehair_multi_dev as dev
    import logging
    setupDefaultLogger("D:/log/log3.log")
    opts = [100, 200, 300, 400]
    for o in opts:
        e = dev.guideSelect(fileName, o, nFrame, 0,  dev.selectByRandom)
        logging.info("Random, %d guides: %f" % (o, e))
        e =  dev.guideSelect(fileName, o, nFrame, 0,  dev.selectByChai2016)
        logging.info("Chai, %d guides: %f" % (o, e))
