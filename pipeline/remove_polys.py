#!/usr/bin/env python
# -*- coding: utf-8-*-

	
"""
Filename: remove_polys.py

"""


def removePolys(input, output):
    f = open(input)
    f2 = open(output, "w")

    polys = 0
    skip = 0
    for line in f:
        if skip > 0:
            skip -= 1
            continue
        elif "Group" in line:
            polys = 0
        elif "Polygon" in line:
            if polys == 0 or polys == 1:
                skip = 2
                polys +=1
                continue

        f2.write(line)

    f.close()
    f2.close()


if __name__ == '__main__':
    import sys
    removePolys(sys.argv[1], sys.argv[2])

