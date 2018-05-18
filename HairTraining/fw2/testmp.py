from multiprocessing import Process, Value, Array, Pool
import crash_on_ipy
def f(n, a, id):
    n.value = 3.1415927
    if id == 0:
        for i in range(len(a)):
            a[i] = -a[i]
    else:
        for i in range(len(a)/2, len(a)):
            a[i] = -a[i]

    return id

def f1(x):
    print x

if __name__ == '__main__':
    p = Pool()
    p.map(f1, [1,2,3])
    assert(False)