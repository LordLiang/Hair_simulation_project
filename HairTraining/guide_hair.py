import metis_graph as mg

class GroupedGraph(mg.MetisGraph):

    def __init__(self, mgraph, group):

        self.xadj = mgraph.xadj
        self.adjncy = mgraph.adjncy
        self.eweights = mgraph.eweights
        self.hairGroup = group

        self.n_group = max(group)+1
        self.n_strand = len(group)

    def initSolution(self, opt):

        self.createLookupTable()
        self.initGuideHair(opt)

    def createLookupTable(self):
        '''convert the group table into a query link list'''
        self.lookup = []
        for i in range(self.n_group):
            self.lookup.append([])

        for i in range(self.n_strand):
            self.lookup[self.hairGroup[i]].append(i)

    def randomInitGuideHair(self):
        import random
        for i in range(self.n_group):
            if self.guide[i] == None:
                num = self.hairGroup.count(i)
                self.guide[i] = self.lookup[i][int(num*random.random())]

    def initSubOptimizedGuideHair(self):
        for i in range(self.n_strand):
            s = sum(self.eweights[self.xadj[i]:self.xadj[i+1]])
            if s > self.guideVals[self.hairGroup[i]]:
                if s == 0 and self.xadj[i] == self.xadj[i+1]:
                    continue
                self.guideVals[self.hairGroup[i]] = s
                self.guide[self.hairGroup[i]] = i

    def initWorstGuideHair(self):
        self.guideVals = [1e10] * self.n_group
        for i in range(self.n_strand):
            s = sum(self.eweights[self.xadj[i]:self.xadj[i+1]])
            if s < self.guideVals[self.hairGroup[i]]:
                self.guideVals[self.hairGroup[i]] = s
                self.guide[self.hairGroup[i]] = i

    def initGuideHair(self, opt):
        self.guide = [None] * self.n_group
        self.guideVals = [None] * self.n_group
        if opt == "opt":
            self.needIteration = True
            self.initSubOptimizedGuideHair();
            self.randomInitGuideHair();
        elif opt == "rand":
            self.needIteration = False
            self.randomInitGuideHair();
        elif opt == "worst":
            self.needIteration = False
            self.initWorstGuideHair();
            self.randomInitGuideHair();

        self.energy = self.computeEnergy()

        print "\ninit guides: "
        print "  ", self.guide[:15], "..."
        print "init values: "
        print "  ", self.energy

    def computeEnergy(self, guide=None):
        if guide == None:
            guide = self.guide
        eitr = mg.UndirectedIterator(self)
        result = 0.
        for i, j, weight in eitr:
            if self.validPair(i, j, guide):
                result += weight
        return result

    def isGuideHair(self, id, guide=None):
        if guide == None:
            guide = self.guide
        groupId = self.hairGroup[id]
        return id == guide[groupId]

    def validPair(self, i, j, guide):
        return (self.isGuideHair(i, guide) and (not self.isGuideHair(j, guide))) or \
            (self.isGuideHair(j, guide) and (not self.isGuideHair(i, guide)))

    def contributeForEnergyAsGuideMinusAsNormal(self, i, guide):
        eitr = mg.EdgeIterator(self, i)
        result = 0
        for j, weight in eitr:
            if not self.isGuideHair(j, guide):
                result += weight
            else:
                result -= weight
        return result

    def iterate(self):
        changed = False
        for groupId in range(self.n_group):
            sub = self.contributeForEnergyAsGuideMinusAsNormal(self.guide[groupId], self.guide)
            for curNode in self.lookup[groupId]:
                origin, self.guide[groupId] = self.guide[groupId], curNode
                add = self.contributeForEnergyAsGuideMinusAsNormal(self.guide[groupId], self.guide)
                if add > sub:
                    changed = True
                    self.energy -= sub
                    self.energy += add
                    sub = add
                else:
                    self.guide[groupId] = origin
        return changed

    def solve(self, opt):
        self.initSolution(opt)
        count = 0
        if self.needIteration:
            while 1:
                count += 1
                if not self.iterate():
                    break
                print "\niteration %d" % count
                print self.energy

        print "%d groups:" % len(self.guide)
        print "  ", self.guide[:15], "..."
        print "values: "
        print "  ", self.energy

        self.initGroupNeighbourMap()

        return self.guide

    def initGroupNeighbourMap(self):
        self.groupNeighMap = [None] * self.n_group
        self.groupGuideMap = [None] * self.n_group

        for i in range(self.n_group):
            self.groupNeighMap[i] = set([i])

        eItr = mg.UndirectedIterator(self)
        for i, j, w in eItr:
            gi = self.hairGroup[i]
            gj = self.hairGroup[j]
            self.groupNeighMap[gi].add(gj)
            self.groupNeighMap[gj].add(gi)

        def findGuide(thiz, id):
            return thiz.guide[id]

        for i in range(self.n_group):
            n_neigh = len(self.groupNeighMap[i])
            self.groupGuideMap[i] = map(findGuide, [self]*n_neigh, self.groupNeighMap[i])

    def dumpNeighbourMap(self, fileName):
        import struct
        import array
        with open(fileName+"-"+str(self.n_group)+".neigh", "wb") as out:
            out.write(struct.pack('i', self.n_group))
            for i in range(self.n_group):
                out.write(struct.pack('i', len(self.groupNeighMap[i])))
                array.array('i', list(self.groupNeighMap[i])).tofile(out)
