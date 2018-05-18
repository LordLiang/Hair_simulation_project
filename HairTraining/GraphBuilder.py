from scipy.spatial import cKDTree

def createKDTree(n_pts, data):
    kdt = cKDTree(data.data)
    return kdt

def createInitGraphLoop(radius, frame, edgeHash, i, factor):
    kdt = createKDTree(frame.n_particle, frame)
    pairs = kdt.query_pairs(radius)
    # filter with index
    tmp = []
    for pair in pairs:
        if (pair[1]-pair[0]) % factor == 0:
            tmp.append(pair)
    pairs = tmp

    if i == 0:
        edgeHash = dict.fromkeys(pairs, None)
        for key in edgeHash.keys():
            edgeHash[key] = 1
        return edgeHash

    for pair in pairs:
        edgeHash.setdefault(pair, 0)
        edgeHash[pair] += 1

    return edgeHash

def filterEdges(edges, thresh):
    trash = []
    before = len(edges)
    for key in edges:
        if edges[key] < thresh:
            trash.append(key)
    for key in trash:
        del edges[key]

    print "Filter edges from %d to %d!" %(before, len(edges))
    return edges

def shrinkGraph(graph, factor):
    smaller = {}
    for key in graph.keys():
        newkey = (key[0]/factor, key[1]/factor)
        if (newkey[0] == newkey[1]):
            continue
        smaller.setdefault(newkey, 0.)
        smaller[newkey] += graph[key]
    print "The graph has only %d edges after shrinking!" % len(smaller)

    return smaller

def normalize(graph, nStep):
    minVal = min(graph.eweights)
    maxVal = max(graph.eweights)
    interval = maxVal - minVal

    print "low %.3f, high %.3f"%(minVal, maxVal)

    for i in range(len(graph.eweights)):
        graph.eweights[i] = int((graph.eweights[i] - minVal) / interval * nStep) + 1
