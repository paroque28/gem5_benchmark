import sys

def eprint(*args):
    sys.stderr.write("".join(args))
    sys.stderr.write("\n")
