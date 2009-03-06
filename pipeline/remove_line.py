#!/usr/bin/env python
# -*- coding: utf-8-*-

	
"""
Filename: remove_rgba.py

"""


def removeRGBA(input, output):
    f = open(input)
    f2 = open(output, "w")

    for line in f:
        if "RGBA" in line:
            continue

        f2.write(line)

    f.close()
    f2.close()


if __name__ == '__main__':
    import sys
    removeRGBA(sys.argv[1], sys.argv[2])

