#! /usr/bin/env python
"""
Module that runs pylint on all python scripts found in a directory tree..
"""
import os
import re
import sys
total = 0.0
count = 0


def check(module):
    """
    Apply pylint to the file specified if it is a *.py file
    """
    global total, count
    if module[-3:] == ".py":
        print("CHECKING  {0}".format(module))
        pout = os.popen('pylint --rcfile=.pylintrc "{0}"'.format(module), 'r')
        for line in pout:
            if re.match("E....:.", line):
                print(line)
            if "Your code has been rated at" in line:
                print(line)
                score = re.findall("\d+.\d\d", line)[0]
                total += float(score)
                count += 1


if __name__ == "__main__":
    try:
        print(sys.argv)
        BASE_DIRECTORY = sys.argv[1]
    except IndexError:
        print(
            "no directory specified, defaulting to current working directory")
        BASE_DIRECTORY = os.getcwd()
    print("looking for *.py scripts in subdirectories of {0}".format(
        BASE_DIRECTORY))
    for root, dirs, files in os.walk(BASE_DIRECTORY):
        if "env" in root:
            continue
        elif "tests" in root:
            continue
        elif "migrations" in root:
            continue
        for name in files:
            filepath = os.path.join(root, name)
            if "pylint-check.py" in filepath:
                continue
            check(filepath)
    print("==" * 50)
    print("{0} modules found".format(count))
    print("AVERAGE SCORE = {0}".format(total / count))
    if (total / count) < 8.0:
        print("Failed Pylint < 8.0")
        exit(1)
    else:
        exit(0)
