from numpy import *
from math import sqrt

# Input: expects Nx3 matrix of points
# Returns R,t
# R = 3x3 rotation matrix
# t = 3x1 column vector

def vector_rotation_3D_non_normalized(ref, cur):
    c = cur / linalg.norm(cur)
    r = ref / linalg.norm(ref)
    return vector_rotation_3D(r, c)

# algorithm: http://math.stackexchange.com/questions/180418/calculate-rotation-matrix-to-align-vector-a-to-vector-b-in-3d
def vector_rotation_3D(ref, cur):
    v = cross(ref, cur);
    s = linalg.norm(v)
    c = dot(ref, cur)
    if abs(s - 0.) < 1e-10:
        if c > 0.:
            return matrix(identity(3))
        else:
            return -matrix(identity(3))

    vx = matrix([[0, -v[2], v[1]],
    [v[2], 0, -v[0]], [-v[1], v[0], 0]])

    R = identity(3) + vx + vx*vx*(1-c)/s/s
    return R

def rigid_transform_3D(A, B):
    '''A=reference state, B=current state'''
    assert len(A) == len(B)

    N = A.shape[0]; # total points

    centroid_A = mean(A, axis=0)
    centroid_B = mean(B, axis=0)

    # centre the points
    AA = A - tile(centroid_A, (N, 1))
    BB = B - tile(centroid_B, (N, 1))

    # dot is matrix multiplication for array
    H = transpose(AA) * BB
    U, S, Vt = linalg.svd(H)
    R = Vt.T * U.T

    # special reflection case
    if linalg.det(R) < 0:
       print "Reflection detected"
       Vt[2,:] *= -1
       R = Vt.T * U.T

    t = -R*centroid_A.T + centroid_B.T
    return R, t.A1

def rigid_trans_full(trans, state):
    return (state[0] * trans[0].T).A1 + trans[1], (state[1] * trans[0].T).A1

def point_trans(trans, state):
    '''trans = (R, t), state = (pos, tan)'''
    return state[0] + trans[1], (state[1] * trans[0].T).A1

def rigid_trans_batch(trans, state):
    '''note this is different from point_trans_batch!!!!!'''
    return (state[0] * trans[0].T).A + tile(trans[1], (len(state[0]), 1)), (state[1] * trans[0].T).A

def rigid_trans_batch_no_dir(trans, state):
    '''note this is different from point_trans_batch!!!!!'''
    return (state * trans[0].T).A + tile(trans[1], (len(state), 1))

def point_trans_batch(trans, state):
    '''trans = (R, t), state = (pos, tan)'''
    plist = []
    dlist = []
    for i in range(len(trans)):
        p, d = point_trans(trans[i], (state[0][i], state[1][i]))
        plist.append(p)
        dlist.append(d)
    return array(plist), array(dlist)

def point_trans_batch_no_dir(trans, state):
    '''trans = (R, t), state = (pos, tan)'''
    plist = []
    for i in range(len(trans)):
        p = trans[i][1] + state[i]
        plist.append(p)
    return array(plist)

def apply_point_trans(trans, state):
    '''trans = (R, t), state = (pos, tan)'''
    state[0] += trans[1]
    state[1] = tan * trans[0].T

def squared_diff(s0, s1):
    diff_pos = s0[0] - s1[0]
    diff_dir = s0[1] - s1[1]
    return diff_pos.dot(diff_pos) + diff_dir.dot(diff_dir)
