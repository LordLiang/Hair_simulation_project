from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import matplotlib.pyplot as plt
import numpy as np
import cPickle as pkl
import metis_graph as mg
import math
import crash_on_ipy

G = pkl.load(file("c0524mgB.dump"))
edges = mg.UndirectedIterator(G)

X = np.arange(0, 1, 0.005)
Y = np.arange(0, 1, 0.005)
Z = np.zeros((len(X),len(Y)))

print len(Z)
diffs = []
for e in edges:
    diff = e[1]-e[0]
    weight = e[2]

    diffs.append(diff)
    diff = diff / 3001.0
    weight = (weight-600) / 402.0

    if diff > 0.999: continue
    if weight < 0.0: continue

    xi = int(math.floor(diff * 200))
    yi = int(math.floor(weight *200))

    Z[xi][yi] += 1


# plt.hist(diffs, 100)
# plt.show()
print len(Z)

plt.imshow(Z, cmap='rainbow')
plt.show()
quit()
import ipdb; ipdb.set_trace()
fig = plt.figure()
ax = fig.gca(projection='3d')

X, Y = np.meshgrid(X, Y)
surf = ax.plot_surface(X, Y, Z.tolist(), rstride=1, cstride=1, cmap=cm.coolwarm,
                       linewidth=0, antialiased=False)
# ax.set_zlim(0, 1.01)
ax.set_ylim(0, 1.1)

ax.zaxis.set_major_locator(LinearLocator(10))
ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))

fig.colorbar(surf, shrink=0.5, aspect=5)

plt.show()
