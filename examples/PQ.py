import numpy as np
from scipy import sparse
from numpy import array


# I = array([0,3,1,0])
# J = array([0,3,1,2])
# V = array([4,5,7,9])
# print I
# print J
# print V
# A = sparse.coo_matrix((V,(I,J)),shape=(4,4))
# print A.todense()


class ReadSparseMatrix:
    def __init__(self, filename):
        self.mat = 0
        # self.users = 0
        self.read_file(filename)

    def read_file(self, filename):
        d = np.loadtxt(filename, delimiter=",")
        s = range(0, 100000, 200)
        d = d[s, :]
        movies = d[:, 0].astype(int)
        movies_ID = (list(set(movies)))
        movie_row_dict = dict(zip(movies_ID, xrange(0, len(movies_ID))))
        row_numbers = array([movie_row_dict[movie] for movie in movies])
        users = d[:, 1].astype(int)
        user_ID = (list(set(users)))
        user_col_dict = dict(zip(user_ID, xrange(0, len(user_ID))))
        col_numbers = array([user_col_dict[user] for user in users])
        mark = d[:, 2].astype(int)
        self.mat = sparse.coo_matrix((mark, (row_numbers, col_numbers)), shape=(len(movies_ID), len(user_ID))).tolil()
        self.size = (len(set(movies)), len(user_ID))
        self.row_numbers = row_numbers
        self.col_numbers = col_numbers
        print self.mat.shape
        #print self.mat.shape
        #print self.mat[0:10, 0:10].shape

    def calc_error(self, P, Q):
        err = 0
        items = 0
        for r in self.row_numbers:
            for c in self.col_numbers:
                if self.mat[r, c] > 0:
                    items += 1
                    err = err + (self.mat[r, c] - np.dot(P[r, :], Q[:, c])) ** 2
        return 1./items * np.sqrt(err)
        #return err



class MiniBatchProccesing:
    def __init__(self, R, factors_num, peace_row, peace_col):
        P = np.random.rand(R.shape[0], factors_num)
        Q = np.random.rand(factors_num, R.shape[1])
        self.index_raw = [i * peace_row for i in xrange(0, R.shape[0]/peace_row + 1) if i * peace_row < R.shape[0]]
        self.index_raw.append(R.shape[0])
        self.index_col = [i * peace_col for i in xrange(0, R.shape[1]/peace_col + 1) if i * peace_col < R.shape[1]]
        self.index_col.append(R.shape[1])
        steps = 100
        alpha = 0.02
        beta = 0.02
        #print P.shape
        #print Q.shape
        for st in xrange(steps):
            for i in xrange(0, len(self.index_raw) - 1):
                for j in xrange(0, len(self.index_col) - 1):
                    # these two loops is iterating among batches
                    P, Q = self.gradient_step(alpha, beta,
                                              R[
                                                self.index_raw[i]:self.index_raw[i+1],
                                                self.index_col[j]:self.index_col[j+1]
                                              ], P, Q,
                                              self.index_raw[i], self.index_col[j]
                                              )
        self.P = P
        self.Q = Q


    def error(self, R, P, Q, i0, j0):
        # this R was obtained by slicing from original
        err = 0
        for i in xrange(R.shape[0]):
            for j in xrange(R.shape[1]):
                if R[i, j] > 0:
                    err = err + (R[i, j] - np.dot(P[i0 + i, :], Q[:, j0 + j])) ** 2
        #err = 1
        return err

    def gradient_step(self, alpha, beta, R, P, Q, i0, j0):
        # this R was obtained by slicing from original
        for i in xrange(R.shape[0]):
            for j in xrange(R.shape[1]):
                if R[i, j] > 0:
                    for m in xrange(len(P[0])):
                        Jij = -2 * (R[i, j] - np.dot(P[i0 + i, :], Q[:, j0 + j]))
                        P[i0 + i][m] = P[i0 + i][m] - alpha * (Jij * Q[m][j0 + j] + beta * P[i0 + i][m])
                        Q[m][j0 + j] = Q[m][j0 + j] - alpha * (Jij * P[i0 + i][m] + beta * Q[m][j0 + j])
        return P, Q





R = [
    [5, 3, 0, 1],
    [4, 0, 3, 1],
    [1, 1, 0, 5],
    [1, 0, 0, 0],
    [0, 1, 5, 4],
]
R = array(R)
N = len(R)
M = len(R[0])
K = 2

P = np.random.rand(N, K)
Q = np.random.rand(K, M)

read_sparse = ReadSparseMatrix("net_fl_data.txt")
mini_batch_processing = MiniBatchProccesing(read_sparse.mat, 2, 10, 50)
print read_sparse.calc_error(mini_batch_processing.P, mini_batch_processing.Q)
#print np.dot(mini_batch_processing.P, mini_batch_processing.Q)

#P1, Q1 = matrix_factorization(R, P, Q)

#print R
#print np.dot(P1, Q1)
#print P, Q
