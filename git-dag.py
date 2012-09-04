#!/usr/bin/python

import random
import subprocess
import sys

# Problem: Say we have some branch B and a root branch R.  So the
# "depends on" relationship on the commits in R..B is a partial ordering,
# and R is the bottom element of this ordering.
#
# We're given a single topological sort of the elements of B. (We get
# it with 'git log R..B')
#
# We have an oracle that can tell us whether some subsequence of R..B
# is a "valid branch" (it is a topologically sorted sequence that
# contains every dependency of every one of its members).
#
# We want to learn the original partial ordering.


# Find what commits to look for dependencies between

# Find all commits in that sequence

# Define the empty set as successful.
# For each commit i in the sequence, define the set 0..i as successful.

# For any other set of commits, that set is successful if and only if
#    the subsequence of the original sequence containing only commits
#    from that set, applies in order and passes some given test.
#    Evaluate this lazily.



class DependencyLearner:
    def __init__(self, n_items):
        self._N = n_items
        self._success_map = {}
        self._reqs = []

        for i in xrange(n_items + 1):
            self._success_map[(1<<i)-1] = True

    def _requirement_closure(self, seq, n):
        r = 0
        for i in xrange(n):
            b = seq & 1
            if b:
                # XXX this will need work if _reqs can be multiple.
                r |= self._reqs[i]
            seq >>= 1
        return r

    def sequenceIsValid(self, seq):
        raise NotImplemented("sequenceIsValid")

    def _successful(self, seq):
        try:
            return self._success_map[seq]
        except KeyError:
            return self.sequenceIsValid(seq)

    def _find_requirements(self, i):
        r = None
        rbits = i+10 # stupid overflow to avoid problems
        bit = 1<<i
        for n_pred in xrange(i+1):
            for seq in _combinations(i, n_pred):
                attempt = self._requirement_closure(seq, i)
                attempt |= bit

                bits_set = _bitcount(attempt)
                if self._successful(attempt):
                    if bits_set < rbits:
                        r = [ seq | bit ]
                        rbits = bits_set
                    elif bits_set == rbits:
                        r.append( seq | bit )
            if r is not None:
                break
        return r

    def solve(self):
        self._reqs = []
        for i in xrange(self._N):
            r = self._find_requirements(i)
            # XXXX should allow for remembering other values.
            self._reqs.append(r[0])

        return self._reqs[:]

# yield all n-bit values with b bits set.
def _combinations(n, b):
    if b == 0:
        yield 0
    elif b > n:
        return
    elif b == 1:
        for i in xrange(n):
            yield 1<<i
    elif b == n:
        yield (1<<(n+1)) - 1
    else:
        for i in xrange(n):
            bit = (1<<i)
            for v in _combinations(i, b-1):
                yield v | bit

_BYTE_BITS = [ "{0:b}".format(i).count("1") for i in range(256) ]
# return the number of bits set in 'val'
def _bitcount(val):
    bb = _BYTE_BITS
    r = 0
    while val:
        b = val & 255
        val >>= 8
        r += bb[b]
    return r


class DemoDepLearner(DependencyLearner):
    #   A <- B <- C
    #     <- D <- E
    #     <- F
    def sequenceIsValid(self, s):
        a = s & 1
        b = s & 2
        c = s & 4
        d = s & 8
        e = s & 16
        f = s & 32
        if (b or d or f) and not a:
            return False
        if c and not b:
            return False
        if e and not d:
            return False
        return True


DDL = DemoDepLearner(6)
r = DDL.solve()

for i in xrange(len(r)):
    output = r[i]
    print "{0:06b}".format(1<<i), "-> ", "{0:06b}".format(output)

