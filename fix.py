#!/usr/bin/python
import sys
from settings import * #my settings

# (works)
# cat S355Cnov29th2006.dat | python testio.py > iamIO.txt
# for i in `ls *.dat`; do cat $i | python ../../newest/fix.py > $i.txt; done


def int2bin(n, count=8):
    """returns the binary of integer n, using count number of digits"""
    return "".join([str((n >> y) & 1) for y in range(count-1, -1, -1)])

def even_parity_check(bin):
	"""checks if 8 bit string of 1's & 0's computes to even parity"""
	return int(bin[0],2) == (int(bin[1],2) ^ int(bin[2],2) ^ int(bin[3],2) ^ int(bin[4],2) ^ int(bin[5],2) ^ int(bin[6],2) ^ int(bin[7],2))


header = "P#,PID,S#,TIME,CPMA,A:2S%,A:%REF,CPMB,B:2S%,B:%REF,CPMC,C:2S%,C:%REF,SIS,DPM1,DPM2,ELTIME,FLAG,tSIE\n"

#f = open(sys.stdin, 'rb')
data = sys.stdin.read()
mod = ''

for char in data:
	num = ord(char)
	bin = int2bin(num, 8)
	if not(even_parity_check(bin)): raise IOError, 'Parity Check Failed' ###print "~"
	strip = bin[1:8]
	pad = '0' + strip
	gobacktoint = int(pad, 2)
	mod+= chr(gobacktoint)

saved = ''
data = mod.split('\n')


for line in data:

	if line != '':


		where = line.find(',EOP')
		if where > 0:
		#if line[-4:] == ',EOP': #last 4 characters
			saved = saved + '---protocol #: %s ended.---\n' % int(line[0:where])


		elif line[0:2] == 'S,':
			pass

		else:
			split = line.split(',')

			if (len(split) >= 4) and split[3] in ['SIS', 'tSIE', 'tSIE\AEC']:
				pass #this is a header


			elif len(split) == len(cells)-1: # -1 b/c no CRLF in split data
				#regular data... do something with it...
				saved = saved + ','.join(split) + '\n'

			else:
				pass


sys.stdout.write(header + saved)





