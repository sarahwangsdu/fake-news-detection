class Node:
    isVisited = False
    neighbour = []

    def __init__(self):
        self.isVisited = False
        self.neighbour = []

    def traverseDFT(self):
        if self.isVisited:
            return
        self.isVisited = True
        for i in range(0, len(self.neighbour)):
            self.traverseDFT(self.neighbour[i])
        return

    def traverseBFT(self):
        queue =[]
        tempNode = None
        queue.append(self)
        while len(queue) > 0:
            tempNode = queue.pop()
            tempNode.isVisited = True
            for i in range(0,len(tempNode.neighbour)):
                if not tempNode.neighbour[i].isVisited:
                    queue.append(tempNode.neighbour[i])
