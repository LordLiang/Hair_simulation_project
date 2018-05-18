
class UndirectedIterator:
    def __init__(self, mgraph):
        self.graph = mgraph

    def __iter__(self):
        self.i = 0
        self.j = -1
        return self

    def next(self): # Python 3: def __next__(self)
        while 1:
            self.j += 1
            if self.j >= len(self.graph.adjncy):
                raise StopIteration
            while self.j >= self.graph.xadj[self.i+1]:
                self.i += 1
            if self.i < self.graph.adjncy[self.j]:
                break
        return self.i, self.graph.adjncy[self.j], self.graph.eweights[self.j]



class DirectedIterator:
    def __init__(self, mgraph):
        self.graph = mgraph

    def __iter__(self):
        self.i = 0
        self.j = -1
        return self

    def next(self): # Python 3: def __next__(self)
        while 1:
            self.j += 1
            if self.j >= len(self.graph.adjncy):
                raise StopIteration
            while self.j >= self.graph.xadj[self.i+1]:
                self.i += 1
        return self.i, self.graph.adjncy[self.j], self.graph.eweights[self.j]


class EdgeIterator:
    def __init__(self, mgraph, node):
        self.graph = mgraph
        self.node = node
        self.start = mgraph.xadj[node]-1
        self.end = mgraph.xadj[node+1]

    def __iter__(self):
        self.cur = self.start
        return self

    def next(self): # Python 3: def __next__(self)
        self.cur += 1
        if self.cur >= self.end:
            raise StopIteration
        return self.graph.adjncy[self.cur], self.graph.eweights[self.cur]

class MetisGraph:
    def __init__(self, mygraph = None, n_vertices = 0):
        if mygraph == None:
            self.xadj = []
            self.adjncy = []
            self.eweights = []
        else:
            self.convertFromMyGraph(mygraph, n_vertices)

    def convertFromMyGraph(self, graph, n_vertices):
        if n_vertices == None or n_vertices <= 0:
            raise Exception("number of vertices must be determined!")

        vstat = [None] * n_vertices
        for i in range(n_vertices):
            vstat[i] = []

        # key tuple has been confirmed from small to large
        keys = graph.keys()
        for key in keys:
            vstat[key[0]].append([key[1], graph[key]])
            vstat[key[1]].append([key[0], graph[key]])

        self.xadj = [None] * (n_vertices+1)
        self.xadj[0] = 0
        self.adjncy = []
        self.eweights = []

        for i in range(n_vertices):
            self.xadj[i+1] = self.xadj[i] + len(vstat[i])
            for edge in vstat[i]:
                self.adjncy.append(edge[0])
                self.eweights.append(edge[1])

    def convertFromMyGraphNoneWeight(self, graph, n_vertices):
        if n_vertices == None or n_vertices <= 0:
            raise Exception("number of vertices must be determined!")

        vstat = [None] * n_vertices
        for i in range(n_vertices):
            vstat[i] = []

        # key tuple has been confirmed from small to large
        keys = graph
        for key in keys:
            vstat[key[0]].append(key[1])
            vstat[key[1]].append(key[0])

        self.xadj = [None] * (n_vertices+1)
        self.xadj[0] = 0
        self.adjncy = []
        self.eweights = []

        for i in range(n_vertices):
            self.xadj[i+1] = self.xadj[i] + len(vstat[i])
            for edge in vstat[i]:
                self.adjncy.append(edge)
