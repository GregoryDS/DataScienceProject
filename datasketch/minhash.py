'''
This module implements MinHash - a probabilistic data structure for computing
Jaccard similarity between datasets.

The original MinHash paper:
http://cs.brown.edu/courses/cs253/papers/nearduplicate.pdf
'''

import random, struct
import numpy as np

# http://en.wikipedia.org/wiki/Mersenne_prime
_mersenne_prime = (1 << 61) - 1
_max_hash = (1 << 32) - 1
_hash_range = (1 << 32)


class MinHash(object):
    '''
    The MinHash object.
    '''

    __slots__ = ('permutations', 'hashvalues', 'seed')

    def __init__(self, num_perm=128, seed=1):
        '''
        Create a MinHash object with `num_perm` number of random
        permutation functions.
        The `seed` parameter controls the set of random permutation functions
        generated for this MinHash object.
        Different seed will generate different sets of permutaiton functions.
        '''
        if num_perm <= 0:
            raise ValueError("Cannot have non-positive number of\
                    permutation functions")
        if num_perm > _hash_range:
            # Because 1) we don't want the size to be too large, and
            # 2) we are using 4 bytes to store the size value
            raise ValueError("Cannot have more than %d number of\
                    permutation functions" % _hash_range)
        self.hashvalues = np.array([_max_hash for _ in range(num_perm)])
        self.seed = seed
        generator = random.Random()
        generator.seed(self.seed)
        # Create parameters for a random bijective permutation function
        # that maps a 32-bit hash value to another 32-bit hash value.
        # http://en.wikipedia.org/wiki/Universal_hashing
        self.permutations = np.array([(generator.randint(1, _mersenne_prime),
                                       generator.randint(0, _mersenne_prime)) 
                                      for _ in range(num_perm)]).T
    
    def is_empty(self):
        '''
        Check if the current MinHash object is empty - at the state of just
        initialized.
        '''
        if np.any(self.hashvalues != _max_hash):
            return False
        return True

    def digest(self, hashobj):
        '''
        Digest a hash object that implemented `digest` as in hashlib,
        and has size at least 4 bytes.
        '''
        # Digest the hash object to get the hash value
        hv = struct.unpack('<I', hashobj.digest()[:4])[0]
        a, b = self.permutations
        phv = np.bitwise_and((a * hv + b) % _mersenne_prime, _max_hash)
        self.hashvalues = np.minimum(phv, self.hashvalues)

    def merge(self, other):
        '''
        Merge the other MinHash object with this one, making this the union
        of both.
        '''
        if other.seed != self.seed:
            raise ValueError("Cannot merge MinHash objects with\
                    different seeds")
        if self.hashvalues.size != other.hashvalues.size:
            raise ValueError("Cannot merge MinHash objects with\
                    different numbers of permutation functions")
        self.hashvalues = np.minimum(other.hashvalues, self.hashvalues)

    def count(self):
        '''
        Estimate the cardinality count.
        See: http://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=365694 
        '''
        k = self.hashvalues.size
        return np.float(k) / np.sum(self.hashvalues / np.float(_max_hash)) - 1.0

    def jaccard(self, other):
        '''
        Estimate the Jaccard similarity (resemblance) between this Minhash
        and the other.
        '''
        if other.seed != self.seed:
            raise ValueError("Cannot compute Jaccard given MinHash objects with\
                    different seeds")
        if self.hashvalues.size != other.hashvalues.size:
            raise ValueError("Cannot compute Jaccard given MinHash objects with\
                    different numbers of permutation functions")
        return np.float(np.count_nonzero(self.hashvalues==other.hashvalues)) /\
                np.float(self.hashvalues.size)

    def bytesize(self):
        '''
        Returns the size of this MinHash object in bytes.
        To be used in serialization.
        '''
        # Use 8 bytes to store the seed integer
        seed_size = struct.calcsize('q')
        # Use 4 bytes to store the number of hash values
        length_size = struct.calcsize('i')
        # Use 4 bytes to store each hash value as we are using 32 bit
        hashvalue_size = struct.calcsize('I')
        return seed_size + length_size + len(self.hashvalues) * hashvalue_size

    def serialize(self, buf):
        '''
        Serializes this MinHash object into bytes, store in `buf`.
        This is more efficient than using pickle.dumps on the object.
        '''
        if len(buf) < self.bytesize():
            raise ValueError("The buffer does not have enough space\
                    for holding this MinHash object.")
        fmt = "qi%dI" % len(self.hashvalues)
        struct.pack_into(fmt, buf, 0,
                self.seed, len(self.hashvalues), *self.hashvalues)

    @classmethod
    def deserialize(cls, buf):
        '''
        Reconstruct a MinHash object from a byte buffer.
        This is more efficient than using the pickle.loads on the pickled
        bytes.
        '''
        try:
            seed, num_perm = struct.unpack_from('qi', buf, 0)
        except TypeError:
            seed, num_perm = struct.unpack_from('qi', buffer(buf), 0)
        mh = cls(num_perm=num_perm, seed=seed)
        offset = struct.calcsize('qi')
        try:
            mh.hashvalues = np.array(struct.unpack_from('%dI' % num_perm,
                buf, offset))
        except TypeError:
            mh.hashvalues = np.array(struct.unpack_from('%dI' % num_perm,
                buffer(buf), offset))
        return mh

    def __getstate__(self):
        '''
        This function is called when pickling the MinHash object.
        Returns a bytearray which will then be pickled.
        Note that the bytes returned by the Python pickle.dumps is not
        the same as the buffer returned by this function.
        '''
        buf = bytearray(self.bytesize())
        self.serialize(buf)
        return buf

    def __setstate__(self, buf):
        '''
        This function is called when unpickling the MinHash object.
        Initialize the object with data in the buffer.
        Note that the input buffer is not the same as the input to the
        Python pickle.loads function.
        '''
        try:
            seed, num_perm = struct.unpack_from('qi', buf, 0)
        except TypeError:
            seed, num_perm = struct.unpack_from('qi', buffer(buf), 0)
        self.__init__(num_perm=num_perm, seed=seed)
        offset = struct.calcsize('qi')
        try:
            self.hashvalues = np.array(struct.unpack_from('%dI' % num_perm,
                buf, offset))
        except TypeError:
            self.hashvalues = np.array(struct.unpack_from('%dI' % num_perm,
                buffer(buf), offset))

    @classmethod
    def union(cls, *mhs):
        '''
        Return the union MinHash of multiple MinHash objects
        '''
        if len(mhs) < 2:
            raise ValueError("Cannot union less than 2 MinHash sketches")
        num_perm = mhs[0].hashvalues.size
        seed = mhs[0].seed
        if any(seed != m.seed for m in mhs) or \
                any(num_perm != m.hashvalues.size for m in mhs):
            raise ValueError("The unioning MinHash objects must have the\
                    same seed and number of permutation functions")
        mh = cls(num_perm=num_perm, seed=seed)
        mh.hashvalues = np.minimum.reduce([m.hashvalues for m in mhs])
        return mh

    def __eq__(self, other):
        '''
        Check equivalence between MinHash objects
        '''
        return self.seed == other.seed and \
                np.array_equal(self.hashvalues, other.hashvalues)


def jaccard(*mhs):
    '''
    Compute Jaccard similarity measure for multiple of MinHash objects.
    '''
    if len(mhs) < 2:
        raise ValueError("Less than 2 MinHash objects were given")
    seed = mhs[0].seed
    if any(seed != m.seed for m in mhs):
        raise ValueError("Cannot compare MinHash objects with\
                different seeds")
    num_perm = mhs[0].hashvalues.size
    if any(num_perm != m.hashvalues.size for m in mhs):
        raise ValueError("Cannot compare MinHash objects with\
                different numbers of permutation functions")
    if len(mhs) == 2:
        m1, m2 = mhs
        return np.float(np.count_nonzero(m1.hashvalues == m2.hashvalues)) /\
                np.float(m1.hashvalues.size)
    # TODO: find a way to compute intersection for more than 2 using numpy
    intersection = 0
    for i in range(num_perm):
        phv = mhs[0].hashvalues[i]
        if all(phv == m.hashvalues[i] for m in mhs):
            intersection += 1
    return float(intersection) / float(num_perm)
