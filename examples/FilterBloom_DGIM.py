from bitarray import bitarray
from random import random
from struct import *
from bitstring import BitArray
import math
import hashlib

class DGIM:
    PACK_STR = 'Ih'

    def __init__(self, barray, k):
        self.barray = barray
        # subwindow for calculating average value
        self.k = k
        # contains pairs which represent buckets
        self.lst = []
        self.first_buckets_init()

    def find_first_1(self, time_stamp):
        for i in reversed(xrange(time_stamp)):
            if self.barray[i]:
                return i
        return len(self.barray)

    def first_buckets_init(self):
        #
        bound_stamp_position = len(self.barray) - 1 - self.k
        last_stamp = self.find_first_1(len(self.barray))
        power_counter = 0
        position = last_stamp
        self.lst.append([BitArray(bin(last_stamp)), BitArray(bin(1))])
        last_stamp = self.find_first_1(position)
        position = last_stamp
        while last_stamp > bound_stamp_position:
            power_counter += 1
            size = 2**power_counter
            num_of_ones = 0
            # creating the list of buckets
            for i in reversed(xrange(last_stamp + 1)):
                if num_of_ones == size:
                    self.lst.append([BitArray(bin(last_stamp)), BitArray(bin(size))])
                    break
                elif self.barray[i]:
                    num_of_ones += 1
                position -= 1
            last_stamp = self.find_first_1(position + 1)

    def print_lst(self):
        for l in self.lst:
            print '(', l[0].uint, l[1].uint, ')'

    def real_ones_number(self):
        len_b = len(self.barray)
        return sum(self.barray[len_b - self.k:])

    def get_the_estimated_value(self):
        return sum(map(lambda x: x[1].uint, self.lst[0:-1])) + 1./2 * self.lst[-1][1].uint

    def decrease_time_stamps(self):
        for i, l in enumerate(self.lst):
            bucket = [l[0].uint, l[1].uint]
            bucket[0] -= 1
            self.lst[i] = [BitArray(bin(bucket[0])), BitArray(bin(bucket[1]))]

    def shift_the_window(self):
        # delete last element in window
        len_b = len(self.barray)
        del self.barray[0]
        # add new element to window
        self.barray.append(random() < 0.5)
        self.decrease_time_stamps()
        last_bucket = [self.lst[-1][0].uint, self.lst[-1][1].uint]
        # if last bucket timestamp smaller then the lentgth of subwindow in which we make calculations
        if last_bucket[0] <= len_b - 1 - self.k:
            del self.lst[-1]
        len_lst = len(self.lst)
        last_size = last_bucket[1]
        quantity_of_buckets_size_of_1 = sum([l[1].uint == 1 for l in self.lst[0:2]])
        if self.barray[-1]:
            self.lst.insert(0, [BitArray(bin(len_b - 1)), BitArray(bin(1))])
        # two cases for quantity_of_buckets_size_of_1 value: 2 and 3
        # first: [1] [1], number = 2, considering
        # second [101] [01], number = 1, nothing to be done
        if self.barray[-1] and quantity_of_buckets_size_of_1 == 2:
            #merge two first
            bucket1 = [self.lst[1][0].uint, self.lst[1][1].uint]
            bucket2 = [self.lst[2][0].uint, self.lst[2][1].uint]
            self.lst[2] = [BitArray(bin(bucket1[0])), BitArray(bin(bucket1[1] + bucket2[1]))]
            del self.lst[1]
            # the new bucket according to obtained "1"
            # self.lst[0] = pack(self.PACK_STR, len_b - 1, 1)
            power = 1
            position = 1
            while 2**power <= last_size:
                if position + 3 <= len_lst:
                    number_of_buck_of_current_size = sum([l[1].uint == 2**power for l in self.lst[position:position + 3]])
                else: number_of_buck_of_current_size = 0
                power+=1
                if number_of_buck_of_current_size == 3:
                    bucket1 = [self.lst[position + 1][0].uint, self.lst[position + 1][1].uint]
                    bucket2 = [self.lst[position + 2][0].uint, self.lst[position + 2][1].uint]
                    self.lst[position+2] = [BitArray(bin(bucket1[0])), BitArray(bin(bucket1[1] + bucket2[1]))]
                    del self.lst[position + 1]
                    position+=1
                else:
                    break

def make_hashfuncs(num_slices, num_bits):
    # taken from https://github.com/jaybaird/python-bloomfilter/blob/master/pybloom/pybloom.py

    if num_bits >= (1 << 31):
        fmt_code, chunk_size = 'Q', 8
    elif num_bits >= (1 << 15):
        fmt_code, chunk_size = 'I', 4
    else:
        fmt_code, chunk_size = 'H', 2
    total_hash_bits = 8 * num_slices * chunk_size
    if total_hash_bits > 384:
        hashfn = hashlib.sha512
    elif total_hash_bits > 256:
        hashfn = hashlib.sha384
    elif total_hash_bits > 160:
        hashfn = hashlib.sha256
    elif total_hash_bits > 128:
        hashfn = hashlib.sha1
    else:
        hashfn = hashlib.md5
    fmt = fmt_code * (hashfn().digest_size // chunk_size)
    num_salts, extra = divmod(num_slices, len(fmt))
    if extra:
        num_salts += 1
    salts = tuple(hashfn(hashfn(pack('I', i)).digest()) for i in xrange(num_salts))
    def _make_hashfuncs(key):
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        else:
            key = str(key)
        i = 0
        for salt in salts:
            h = salt.copy()
            h.update(key)
            for uint in unpack(fmt, h.digest()):
                yield uint % num_bits
                i += 1
                if i >= num_slices:
                    return

    return _make_hashfuncs

class BloomFilter:

    def __init__(self, set_size, hash_func_number):
        self.size = set_size
        self.hash_number = hash_func_number
        #error_rate = (1 - math.exp(-k*m/n))**k
        self.bits_per_slice = self.size
        self.make_hashes = make_hashfuncs(self.hash_number, self.size)
        self.bits = bitarray(self.bits_per_slice * hash_func_number)
        self.bits.setall(False)

    def add_elem_to_check_set(self, elem):
        hashes = self.make_hashes(elem)
        offset = 0
        for k in hashes:
            self.bits[offset + k] = True
            offset += self.bits_per_slice

    def check_elem_in_set(self, elem):
        hashes = self.make_hashes(elem)
        offset = 0
        for k in hashes:
            if not self.bits[offset + k]:
                return False
            offset += self.bits_per_slice
        return True


def demo_dgim():
    b = bitarray('1011001000111111010100')
    print b
    dgim = DGIM(b, 10)
    print "bucket"
    dgim.print_lst()
    print "estimated", dgim.get_the_estimated_value()
    print "real", dgim.real_ones_number()
    # Shifting window
    for i in xrange(5):
        dgim.shift_the_window()
        print len(dgim.barray)
        print dgim.barray
        print "bucket"
        dgim.print_lst()
        print "estimated", dgim.get_the_estimated_value()
        print "real", dgim.real_ones_number()


def demo_bloom():
    set_size = 1000
    hashes_number = 5
    bloom_filter = BloomFilter(set_size, hashes_number)
    for i in xrange(set_size):
        bloom_filter.add_elem_to_check_set(i)
    #print "number of ones", sum(bloom_filter.bits) / float(bloom_filter.hash_number * bloom_filter.size)

    x = [bloom_filter.check_elem_in_set(i) for i in xrange(1000, 2020)]
    print "real rate", float(sum(x))/ len(x)

    print "theoretical error rate", (1 - math.exp(-1))**hashes_number




def make_rand_bits(N):
    a = bitarray()
    for _ in xrange(0, N):
        a.append(random() < 0.5)
    return a


if __name__ == "__main__":
    demo_dgim()