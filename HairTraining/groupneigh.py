import cPickle as pkl
import struct
import ipdb
import sys
import array
import crash_on_ipy

if __name__ == "__main__":

    import getopt
    try:
        (opts, args) = getopt.getopt(sys.argv[1:], "f:,o:")
    except getopt.error:
        print "wrong args"

    if len(opts) != 0:
        for o,a in opts:
            if o == "-f":
                fileName = a
            elif o == "-o":
                outName = a
    print fileName, outName

    guide, weights = pkl.load(file(fileName, "rb"))
    with open(outName, "wb") as out:
        out.write(struct.pack('i', len(weights)))
        for item in weights:
            if item[0] == None:
                out.write(struct.pack('i', 0))
            else:
                out.write(struct.pack('i', len(item[0])))
                array.array('i', item[1]).tofile(out)
                array.array('f', item[0].flatten()).tofile(out)
