import sys, crash_on_ipy
sys.path.extend(["./fw2"])
import nCache
sys.path.pop()

cache = nCache.CacheFile(r"D:/Data/modelimport/cache/curly20k/rest/rest.xml", 5)

import ipdb; ipdb.set_trace()