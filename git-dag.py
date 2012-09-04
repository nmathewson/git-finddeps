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

def union(s1, s2):
    return s1 | s2

success_map = {}
def successful(s):
    try:
        return success_map[s]
    except KeyError:
        pass

    return the_answer(s)

# Here's our secret:
#     
#   A <- B <- C
#     <- D <- E
#     <- F
def the_answer(s):
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

def populate_success_map(n):
    for i in xrange(n+1):
        success_map[(1<<i) - 1] = True

populate_success_map(6)

# combinations all n-bit values with b bits set.
def combinations(n, b):
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
            for v in combinations(i, b-1):
                yield v | bit


requires = []

def closure(seq, n):
    r = 0
    for i in xrange(n):
        b = seq & 1
        if b:
            r |= requires[i]
        seq >>= 1
    return r

BYTE_BITS = [ "{0:b}".format(i).count("1") for i in range(256) ]
def bitcount(val):
    bb = BYTE_BITS
    r = 0
    while val:
        b = val & 255
        val >>= 8
        r += bb[b]
    return r

def find_requirements(i):
    r = None
    rbits = i+10 # stupid overflow to avoid problems
    bit = 1<<i
    for n_pred in xrange(i+1):
#        print 'n_pred==', n_pred, "bit ==", bit
        for seq in combinations(i, n_pred):
            attempt = closure(seq, i)
            attempt |= bit

            bits_set = bitcount(attempt)
            if successful(attempt):
                if bits_set < rbits:
                    r = [ seq | bit ]
                    rbits = bits_set
                elif bits_set == rbits:
                    r.append( seq | bit )
        if r is not None:
            break
    return r

for i in xrange(6):
    output = find_requirements(i)
    print "{0:06b}".format(1<<i), "-> ", (" ".join("{0:06b}".format(o) for o in output))
    requires.append( output[0] )

# for i = 1..N, where N is the length of the sequence.
#   Let C = S_i
#   For n = 0..i-1:
#      For SS in (all n-element subsequences of S_i..n):
#         Let SS' = the union of 

#      Consider each n-element subsequences SS of the original
#         sequence preceding C:
#            If 
#         Let SS' = SS + C.
#         If
#      If we now know any 





# Start with [] in min-chains set.
# Start with [] in the valid-chains set.
# Start with all commits in unsorted-commits set.
# Start with considered-chains-len = 0.

# While there are unsorted-commits:
#    Let PRED = all 
#    Let 
#    For each unsorted commit U:
#      If there is a valid chain CH of length N-1, try CH-


#    While new-chains:
#       - Try each unsorted-commit on each new-chain  For each such success,
#         add (newchain + unsorted-commit) to new-chains, and remove that
#         unsorted commit from unsorted-commits.
