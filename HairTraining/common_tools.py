import os


def setReadOnly(fileName):
    os.system('attrib +r \"'+fileName+'\"')

def getDefaultLogger(fileName, lvl=None):
    import logging
    logObj = logging.getLogger()

    if not lvl: lvl = logging.DEBUG
    logging.basicConfig(filename=fileName, level=lvl, \
        format='%(levelname)s:%(message)s')

    return logObj

def renameWithBase(name, length=3):
    import os
    import glob

    tmp = name.split('.')
    if len(tmp) == 1:
        prefix = name
        postfix = ''
    elif len(tmp) == 2:
        prefix = tmp[0]
        postfix = '.'+tmp[1]
    else: raise Exception("wrong format", tmp)

    stdLength = len(name)+length
    form = prefix+'?'*length + postfix

    alls = glob.glob(form)
    if len(alls) == 0:
        middle = '0'*length
    else:
        middle = int(alls[-1][len(prefix):len(prefix)+length]) + 1
        if len(str(middle)) > length:
            raise Exception("out of range.", middle, length)
        form = '{:0'+str(length)+'d}'
        middle = form.format(middle)

    return prefix +  middle + postfix


def writeBinary(f, para, content):
    from struct import pack
    f.write(pack(para, content))

def writeInt(f, content):
    writeBinary(f, 'i', content)

def writeFloat(f, content):
    writeBinary(f, 'f', content)

def readBinary(f, para):
    from struct import unpack
    return unpack(para, f.read(4))

def readInt(f):
    return readBinary(f, 'i')[0]

def readFloat(f):
    return readBinary(f, 'f')[0]

if __name__ == "__main__":
    import os

    os.chdir('testFolder')
    for i in range(100):
        f = open(renameWithBase("test.aa"),'w')
        f.close()

    os.system("pause")

    import glob
    for f in glob.glob("test*.aa"):
        os.system("del "+f)
