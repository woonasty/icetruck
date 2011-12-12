#!/usr/bin/env python


import os, sys, argparse


def actualConversion(name):
    cmd = 'iconv -f UTF-16 -t UTF-8 %s > %s.formatted' % (name,name)
    try:
        os.system(cmd)
        print 'converted(utf-16 to utf-8) %s ---> %s.formatted' % (name,name)
    except:
        print 'Error: unable to fetch data'
        print sys.exc_info()[0]

def checkConversion(name):
    cmd = 'file --mime %s' % (name)
    check = os.popen(cmd)
    holder = check.read()
    if 'utf-16' in holder: 
        print 'utf-16 is in this beast'
        print 'sending to conversion function..'
        actualConversion(name)
    else:
        print 'no utf-16, nothing to see here; move along..'

def arglines():
    parser = argparse.ArgumentParser(description="MLBN UTF-16 to UTF-8 converter", version='1.0alpha')
    parser.add_argument('--name', action='store', dest='name',
                        help='name of file to convert')
    args = parser.parse_args()
    print 'sending args.name to checkConversion()'
    checkConversion(args.name)
    return 

if __name__ == "__main__":
    arglines()
