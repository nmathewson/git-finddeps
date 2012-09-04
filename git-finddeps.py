#!/usr/bin/python

import random
import subprocess
import sys
import os

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
                r |= self._cloreqs[i]
            seq >>= 1
        return r

    def sequenceIsValid(self, seq):
        raise NotImplemented("sequenceIsValid")

    def _successful(self, seq):
        try:
            return self._success_map[seq]
        except KeyError:
            outcome = self.sequenceIsValid(seq)
            self._success_map[seq] = outcome
            return outcome

    def _find_requirements(self, i):
        r = None
        rbits = i+10 # stupid overflow to avoid problems
        bit = 1<<i
        for n_pred in xrange(i+1):
            print n_pred, "at a time",
            for seq in _combinations(i, n_pred):
                attempt = self._requirement_closure(seq, i)
                attempt |= bit

                bits_set = _bitcount(attempt)
                #print "looking at {0:b} for {1:b}".format(attempt,(seq|bit))
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
        self._cloreqs = []
        for i in xrange(self._N):
            print "\nPlacing item",i
            r = self._find_requirements(i)
            # XXXX should allow for remembering other values.
            self._reqs.append(r[0])
            self._cloreqs.append(self._requirement_closure(r[0],i) | (1<<i))
            #print "---> {0:b} {1:b}".format(r[0], self._cloreqs[-1])

        return self._reqs[:]

    def getResult(self):
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


# Find what commits to look for dependencies between
def parseCommandLine(argv):
    if len(sys.argv) == 2:
        return sys.argv[2], whereami()
    elif len(sys.argv) == 3:
        return sys.argv[1:]
    else:
        raise UsageError()

# Find all commits in that sequence
def listCommits(a,b):
    out = subprocess.check_output(["git", "rev-list", "--no-merges", "^"+a, b])
    return out.split()

# Stash our current location
def whereami():
    out = subprocess.check_output(["git", "symbolic-ref", "-q", "HEAD"]).strip()
    if out and out.startswith("refs/heads/"):
        return out[len("refs/heads/"):]
    else:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).strip()

# restore our location
def goback(location):
    subprocess.check_output(["git", "checkout", "-q", location])

# name a temporary branch
_temp_counter = 0
def name_temp_branch():
    global _temp_counter
    _temp_counter += 1
    return "gitdag-%s-%s"%(os.getpid(), _temp_counter)

class GitDependencyLearner(DependencyLearner):
    def __init__(self, basis, commitList):
        DependencyLearner.__init__(self, len(commitList))
        self._basis = basis
        self._commits = commitList[:]
        self._branches = []

    def sequenceIsValid(self, seq):
        sys.stdout.write(".")
        sys.stdout.flush()
        if len(self._branches):
            b = self._branches[-1]
        else:
            b = None

        branchName = name_temp_branch()
        self._branches.append(branchName)
        subprocess.check_call(["git", "branch", branchName, self._basis])
        subprocess.check_call(["git", "checkout", "-q", branchName])

        if b:
            subprocess.call(["git", "branch", "-D", b], stdout=subprocess.PIPE)
            del self._branches[-2]

        i = 0
        theseCommits = []
        seq_orig = seq
        while seq:
            bit = seq & 1
            seq >>= 1
            commit = self._commits[i]
            i += 1
            if bit:
                theseCommits.append(commit)

        #print "trying {0:b}".format(seq_orig),

        try:
            subprocess.check_call(["git", "cherry-pick"]+theseCommits,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            #print "THAT WORKED."
            return True
        except subprocess.CalledProcessError:
            subprocess.check_call(["git", "cherry-pick", "--abort"])
            #print "ng"
            return False


    def cleanBranches(self):
        for b in self._branches:
            assert b.startswith("gitdag-")
            subprocess.call(["git", "branch", "-D", b])

    def display(self):
        result = self.getResult()
        for i in xrange(self._N):
            c = self._commits[i]
            r = result[i]
            print c, "===>"
            for j in xrange(i):
                if r & (1<<j):
                    print "\t",self._commits[j]

def run(argv):
    GDL = None
    try:
        started_at = whereami()
        basis, target = parseCommandLine(argv)
        commits = listCommits(basis, target)
        print "Looking at %d commits"%len(commits)
        GDL = GitDependencyLearner(basis, commits)
        GDL.solve()
        GDL.display()

    finally:
        goback(started_at)
        if GDL is not None:
            GDL.cleanBranches()

if __name__ == '__main__':
    run(sys.argv)
