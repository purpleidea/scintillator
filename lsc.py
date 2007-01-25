#!/usr/bin/python

#TODO:
#make work in any size terminal (or a terminal > some min size), and also a terminal that resizes...
#mention empty spaces in racks
#hack format of header and display nicely
#format output number data properly
#format prompt nicer
#validate length of display list (so screen doesn't explode)
#find out about why we have 2 kill messages (and how the kill works)
#check that all the locking is done properly
#see if it's okay to run main() within try/catch
#make stdin work
#make save/export button for getting data onto a usb or something...
#put any other text strings into settings file (and implement multi-language)
#fix restore() so that terminal still displays text when typing after a crash
#fix case of all variables to match some sort of sensible pattern
#add modification of user settings while in the program (maybe it could save them to a file too?)
#get adam to check to see if my code is nice

from settings import *
import thread, time, os, curses, sys
lock = thread.allocate_lock()

#validate settings.py file...
try: crlf = ctitle.index('CRLF')
except ValueError:
	print STR_MISSING_CRLF
	sys.exit()

if (CELLS[-1] != crlf) or (CELLS.count(crlf) > 1):
	print STR_MANY_CRLF
	sys.exit()


stdscr = None

signal = 0 #prompt value

#global pid
pid = os.getpid()

#signals
die = False
alive = False
stop = False
stopped = True

#for message queue-ing
pos = 0
queue = []

#sub windows...
winone = None
wintwo = None
winthree = None

#data
header = []
data = []
files = []

#because i'm cool
def clock():
	global stdscr, winx, ctitle, format, CELLS, pid, die, alive, stop, stopped, pos, queue, header, data, files, signal, DISPLAY, TIMELIMIT, unit_timeout, prompt_wait, default_timelimit
	global MSG_TIME, W_HEIGHT, W_WIDTH, W_LBOR, W_RBOR, W_TBOR, W_BBOR, W_LRBOR, W_TBBOR, W_LPAD, W_RPAD, W_TPAD, W_BPAD, W_LRPAD, W_TBPAD
	lock.acquire()
	alive = alive + 1
	lock.release()
	while 1:
		if die:
			lock.acquire()
			alive = alive - 1
			lock.release()
			break

		output = time.strftime('%d/%m/%Y %H:%M:%S')
		lock.acquire()
		winx.addstr(0, W_WIDTH-2-len(output), output, curses.A_REVERSE)
		winx.refresh()
		lock.release()
		time.sleep(0.1)


def messenger():
	global stdscr, winx, ctitle, format, CELLS, pid, die, alive, stop, stopped, pos, queue, header, data, files, signal, DISPLAY, TIMELIMIT, unit_timeout, prompt_wait, default_timelimit
	global MSG_TIME, W_HEIGHT, W_WIDTH, W_LBOR, W_RBOR, W_TBOR, W_BBOR, W_LRBOR, W_TBBOR, W_LPAD, W_RPAD, W_TPAD, W_BPAD, W_LRPAD, W_TBPAD
	lock.acquire()
	alive = alive + 1
	lock.release()

	blanktimer = 0

	while 1:
		if die:
			lock.acquire()
			alive = alive - 1
			lock.release()
			break

		# i hope we don't need a lock just to read the queue.
		if len(queue) > pos:
			bin = int2bin(queue[pos]['level'], 3)
			if int(bin[-3]):
				queue[pos]['text'] = ('*'*3) + ' ' + queue[pos]['text'] + ' ' + ('*'*3) #critical
				queue[pos]['count'] = queue[pos]['count'] * 2

			#give a msg # to each message except first
			if pos == 0:
				cnt = ''
			else:
				cnt = '(' + str(pos) + ') '

			lock.acquire()
			winx.addstr(2, W_LBOR, ' '*(W_WIDTH-W_LRBOR)) #clear
			winx.addstr(2, W_WIDTH-W_LRBOR-len(queue[pos]['text'])-len(cnt), cnt + queue[pos]['text'], curses.A_REVERSE)
			winx.refresh()
			lock.release()
			for x in range(queue[pos]['count']):
				lock.acquire()
				if int(bin[-2]): curses.beep()
				if int(bin[-1]): curses.flash()
				winx.refresh()
				lock.release()
				time.sleep(0.1)

			pos = pos + 1
			blanktimer = 0 #start timer over again

		else: blanktimer = blanktimer + 1
		time.sleep(MSG_TIME) #time between messages

		if blanktimer > 3: #if we want to clear really old messages...
			lock.acquire()
			winx.addstr(2, W_LBOR, ' '*(W_WIDTH-W_LRBOR)) #clear
			winx.refresh()
			lock.release()



def message(text, level=0, count=1):
	# level:
	# 0: normal message
	# 1: flash
	# 2: beep
	# 4: critical

	#therefore flash+beep --> 1+2 = 3
	global stdscr, winx, ctitle, format, CELLS, pid, die, alive, stop, stopped, pos, queue, header, data, files, signal, DISPLAY, TIMELIMIT, unit_timeout, prompt_wait, default_timelimit
	global MSG_TIME, W_HEIGHT, W_WIDTH, W_LBOR, W_RBOR, W_TBOR, W_BBOR, W_LRBOR, W_TBBOR, W_LPAD, W_RPAD, W_TPAD, W_BPAD, W_LRPAD, W_TBPAD
	dict = {'text':text, 'level':level, 'count':count}
	lock.acquire()
	queue.append(dict)
	lock.release()

#check for spaces in racks... alert the user...
def capture():
	global stdscr, winx, ctitle, format, CELLS, pid, die, alive, stop, stopped, pos, queue, header, data, files, signal, DISPLAY, TIMELIMIT, unit_timeout, prompt_wait, default_timelimit, default_timelimit
	global MSG_TIME, W_HEIGHT, W_WIDTH, W_LBOR, W_RBOR, W_TBOR, W_BBOR, W_LRBOR, W_TBBOR, W_LPAD, W_RPAD, W_TPAD, W_BPAD, W_LRPAD, W_TBPAD

	stopped = False
	timeouts = 0

	header = []
	data = []
	again = True #for spectrum messages
	justended = False
	f = None #file object to be...
	p = -1 #protocol number
	td = time.strftime('%d%m%Y_%H%M%S') #start time
	top = '' #what does at top of .csv file
	for i in range(len(CELLS)-1): #we don't want the crlf on the end...
		top = top + ctitle[CELLS[i]]
		if i < len(CELLS) - 2:
			top = top + ','
	ix = 0 #iterates per serial opening... (how many different protocols in this capture sequence, incl. duplicates)
	zix = 0 #how many loops... (debug)

	try:
		global DEV
		if DEV == 'stdin':
			ser = open(sys.stdin, 'r')

		else:
			global BAUDRATE
			#ser = open('/dev/ttyS0', 'rb') #read, binary
			import serial
			ser = serial.Serial(DEV, baudrate=BAUDRATE, timeout=unit_timeout, parity=serial.PARITY_EVEN, bytesize=serial.SEVENBITS) # (baudrate 9600 is the max for lsc)


	except:
		message(STR_PROBLEM_START)
		stopped = True
		return


	message(STR_IS_START)
	while 1:
		zix = zix + 1
		if stop:
			if not(f == None):
				msg = ' INTERRUPT'
				f.write(('#' + msg + '#'*(len(top)-len(msg)-1)) + '\n')
				f.close()
			f = None
			ser.close()
			ser = None
			stopped = True
			message(STR_IS_STOP)
			break


		line = ser.readline() #read a '\n' terminated line (times out in unit_timeout sec)


		if line != '':
			timeouts = 0 #reset counter
			split = []

			#process...
			"""this program expects that settings on the scintillator side match settings from the settings.py file.
			without correct settings, the data might be parsed wrongly, and there might not be any way to warn the user.
			"""

			where = line.find(',EOP')
			if where > 0:
#			if line[1:7] == ',EOP' + chr(13) + chr(10): #lsc prints this at the end of a protocol?


				header = [] #get it ready to receive a new header...
				data = []
				if not(f == None):
					msg = ' ENDOFFILE'
					f.write(('#' + msg + '#'*(len(top)-len(msg)-1)) + '\n')
					f.close()
					justended = True #tell timeout thing that a protocol just ended...
					timeouts = ((TIMELIMIT/unit_timeout)+1) + 1 #let's not wait anymore for prompt...
				f = None
				p = -1
				message(STR_PROTOCOL_END % int(line[0:where]))
				again = True #reset spectrum message

			elif line[0:2] == 'S,':
				#skips spectrum data at the moment :(
				if again:
					message(STR_FOUND_SPECTRUM)
					again = False # max 1 spectrum data msg per

			else:
				split = line.split(',')

				#TODO: modify split... ie: add the 0 onto the beginning of .543


				# we need to identify if we have a header, and where it is.
				# current logic is to look where the QIP value is supposed to be...
 				# this can be changed if we see any anomalies.
				if (len(split) >= 4) and (split[3] in ['SIS', 'tSIE', 'tSIE\AEC']):
					if len(header) > 0:
						message(STR_ANOTHER_HEADER, 7)

					#TODO: format header nicely, line by line...
					header = ['header: ', split[3], 'header obtained at: %s' % time.strftime('%d/%m/%Y %H:%M:%S')]
					datawindow()


				elif len(split) == len(CELLS)-1: # -1 b/c no CRLF in split data
					#regular data...
					if f == None:

						try: p = ctitle.index('P#')
						except ValueError: p = -1

						try: p = CELLS.index(p) #which cell?
						except ValueError: p = -1

						if p >= 0: p = split[p]
						else:
							p = '~1'

						ix = ix + 1
						files.append('data/lscdata-p%s-%s-%s.csv' % (p, td, ix))
						f = open('data/lscdata-p%s-%s-%s.csv' % (p, td, ix), 'w')
						f.write(top + '\n')


					#optimize the timeout
					try: k = ctitle.index('TIME')
					except ValueError: k = -1

					try: k = CELLS.index(k) #which cell?
					except ValueError: k = -1

					if k >= 0: # and not(DEV == 'stdin')
						k = float(split[k])
						TIMELIMIT = k+2 #2 is guess of some slowness between vials time
					else:
						TIMELIMIT = default_timelimit


					f.write(','.join(split))
					data.append(split)
					datawindow()

				elif line == chr(10): # '\n'
					if justended: #there seems to be a newline all by itself after an *,EOP (is it me or the lsc?)
						pass
					else: message(STR_NEWLINE)


				else:
					#if this keeps coming up, likely select CELLS does not correspond between this program and scintillator
					#if you're sure it matches, or occasionally this pops up, let me know! we have a new type of row :(
					message(STR_UNKNOWN_DATA, 7)
					f_err = open('/tmp/f_err-%s.csv' % (td), 'a')
					f_err.write('start@%s>\n' % zix)
					for Z in range(len(line)):
						f_err.write(str(ord(line[Z])) + '\n')
					f_err.write('<end@%s\n\n' % zix)
					f_err.close()



		else:
			if timeouts > ((TIMELIMIT/unit_timeout)+1):
				#prompt...
				waittime = 0

				lock.acquire()
				winprompt = curses.newwin(W_HEIGHT-W_TBBOR-W_TBPAD-2, W_WIDTH-W_LRBOR-W_LRPAD, 4, 2)
				winprompt.border(0,0,0,0,0,0,0,0)
				winprompt.addstr(0, 2, 'PROMPT', curses.A_REVERSE)
				if justended:
					winprompt.addstr(2, 2, 'a protocol just finished.', curses.A_NORMAL)
					winprompt.addstr(3, 2, 'do you want to wait for another? y/n ?', curses.A_NORMAL)
				else:
					winprompt.addstr(2, 2, 'your capture has timed out.', curses.A_NORMAL)
					winprompt.addstr(3, 2, 'do you want to keep waiting? y/n ?', curses.A_NORMAL)

				winprompt.refresh()
				lock.release()
				signal = 0
				while True:

					time.sleep(1) #wait 1 sec
					waittime = waittime + 1
					if waittime > prompt_wait: signal = ord('y') #so that things can run o/n

					if signal in [ord('y'), ord('Y')]:
						if justended: message(STR_WAITING_PROTOCOL)
						else: message(STR_EXTENDED_TIMEOUT)

						timeouts = 0
						break

					elif signal in [ord('n'), ord('N')]:
						if justended: message(STR_DO_TIMEOUT)
						else: message(STR_TIMEOUT)

						thread.start_new(finish, ()) #try to finish...
						time.sleep(1) #give it a bit of time to finish before we go back in the big while loop...
						break

					lock.acquire()
					if waittime == 15: winprompt.addstr(5, 2, 'please enter y/n', curses.A_NORMAL)
					if waittime % 15 == 0: curses.beep()
					if waittime % 5 == 0: curses.flash()
					winprompt.refresh()
					lock.release()


				winprompt.clear()
				winprompt.refresh()
				winprompt = None


			else: timeouts = timeouts + 1


#try and get the capture thread to shutdown...
def finish():
	global stdscr, winx, ctitle, format, CELLS, pid, die, alive, stop, stopped, pos, queue, header, data, files, signal, DISPLAY, TIMELIMIT, unit_timeout, prompt_wait, default_timelimit
	global MSG_TIME, W_HEIGHT, W_WIDTH, W_LBOR, W_RBOR, W_TBOR, W_BBOR, W_LRBOR, W_TBBOR, W_LPAD, W_RPAD, W_TPAD, W_BPAD, W_LRPAD, W_TBPAD

	if not(stopped):
		message(STR_TRY_STOP)
		stop = True
		signal = ord('n') #in case a prompt is open.
		timer = 0
		while not(stopped): #wait for serial port to close
			if timer > 3*60 + 1:
				message(STR_KILL, 7) #but how is this actually getting done? it doesn't! or maybe it just times out.
				break #okay, i'm not going to wait forever!
			timer = timer + 1
			time.sleep(1)



def helpwindow():

	global stdscr, winx, ctitle, format, CELLS, pid, die, alive, stop, stopped, pos, queue, header, data, files, signal, DISPLAY, TIMELIMIT, unit_timeout, prompt_wait, default_timelimit
	global MSG_TIME, W_HEIGHT, W_WIDTH, W_LBOR, W_RBOR, W_TBOR, W_BBOR, W_LRBOR, W_TBBOR, W_LPAD, W_RPAD, W_TPAD, W_BPAD, W_LRPAD, W_TBPAD
	global winone
	#either create or destroy (toggle)
	if not(winone):
		winone = curses.newwin(W_HEIGHT-W_TBBOR-W_TBPAD-2, W_WIDTH-W_LRBOR-W_LRPAD, 4, 2)
		winone.border(0,0,0,0,0,0,0,0)
		winone.addstr(0, 2, 'HELP/INFO', curses.A_REVERSE)
		header_height = 2
		winone.addstr(2, 2, '%s files have been created (displaying most recent):' % len(files), curses.A_NORMAL)

		for i in range(W_HEIGHT-W_TBBOR-W_TBPAD-2-W_TBBOR-header_height-1):
			winone.addstr(1+i+header_height+1, 1, ' '*(W_WIDTH-W_LRBOR-W_LRPAD-W_LRBOR), curses.A_NORMAL)

		delta = 0 #this ensures we only use the last (newest) values in the files array
		if len(files) > (W_HEIGHT-W_TBBOR-W_TBPAD-W_TBBOR-2-header_height-1):
			delta = len(files) - (W_HEIGHT-W_TBBOR-W_TBPAD-W_TBBOR-2-header_height-1)

		for i in range(min(len(files), W_HEIGHT-W_TBBOR-W_TBPAD-W_TBBOR-2-header_height-1)):
			winone.addstr(1+header_height+1+i, 2, '%s)	%s' % ((len(files)-(i+delta))+1, files[len(files)-(i+delta)]), curses.A_NORMAL)

		winone.refresh()
	else:
		winone.clear()
		winone.refresh()
		winone = None


def datawindow():
	global stdscr, winx, ctitle, format, CELLS, pid, die, alive, stop, stopped, pos, queue, header, data, files, signal, DISPLAY, TIMELIMIT, unit_timeout, prompt_wait, default_timelimit
	global MSG_TIME, W_HEIGHT, W_WIDTH, W_LBOR, W_RBOR, W_TBOR, W_BBOR, W_LRBOR, W_TBBOR, W_LPAD, W_RPAD, W_TPAD, W_BPAD, W_LRPAD, W_TBPAD


	header_height = 0
	if len(header) > 0: #do we have a header?
		header_height = len(header)

	heading = ''
	for i in range(len(DISPLAY)):
		if len(format[DISPLAY[i]]) > len(ctitle[DISPLAY[i]]):
			buf = len(format[DISPLAY[i]]) - len(ctitle[DISPLAY[i]])
		else:
			buf = 0
		heading = heading + ctitle[DISPLAY[i]] + (' '*buf)
		if i < len(DISPLAY) - 1:
			heading = heading + ' '


	global wintwo
	if not(wintwo):
		wintwo = curses.newwin(W_HEIGHT-W_TBBOR-W_TBPAD-2, W_WIDTH-W_LRBOR-W_LRPAD, 4, 2)
		wintwo.border(0,0,0,0,0,0,0,0)
		wintwo.addstr(0, 2, 'DATA', curses.A_REVERSE)
	else:
		#put whitespace over old data to blank
		for i in range(W_HEIGHT-W_TBBOR-W_TBPAD-2-W_TBBOR-header_height-1):
			wintwo.addstr(1+i+header_height+1, 1, ' '*(W_WIDTH-W_LRBOR-W_LRPAD-W_LRBOR), curses.A_NORMAL)

	#print new data
	for i in range(header_height):
		wintwo.addstr(1+i, 2, header[i], curses.A_NORMAL)

	wintwo.addstr(1+header_height, 2, heading, curses.A_NORMAL)

	delta = 0 #this ensures we only use the last (newest) values in the data array
	if len(data) > (W_HEIGHT-W_TBBOR-W_TBPAD-W_TBBOR-2-header_height-1):
		delta = len(data) - (W_HEIGHT-W_TBBOR-W_TBPAD-W_TBBOR-2-header_height-1)

	for i in range(min(len(data), W_HEIGHT-W_TBBOR-W_TBPAD-W_TBBOR-2-header_height-1)):

		row = ''
		for j in range(len(DISPLAY)):

			if DISPLAY[j] in CELLS:
				str = data[i+delta][ CELLS.index(DISPLAY[j]) ]
				#TODO: either this happens here or up at the data capture...
				#str = formatsomehow(str) #format the str to add the 0 in front of an empty decimal?
				if ( len(str) > len(format[DISPLAY[j]]) ):
					row = row + str[0:len(format[DISPLAY[j]])-1] + '#' #show that it doesn't fit by including all but last char and replacing that with a hash (#)

				else:
					if len(format[DISPLAY[j]]) > len(str):
						buf = len(format[DISPLAY[j]]) - len(str)
					else:
						buf = 0

					row = row + str + (' '*buf)

			else:
				row = row + '?' * len(format[DISPLAY[j]]) #value doesn't exist in output CELLS


			if j < len(DISPLAY) - 1:
				row = row + ' '


		wintwo.addstr(1+header_height+1+i, 2, row, curses.A_NORMAL)

	wintwo.refresh()


def setupwindow():

	global stdscr, winx, ctitle, format, CELLS, pid, die, alive, stop, stopped, pos, queue, header, data, files, signal, DISPLAY, TIMELIMIT, unit_timeout, prompt_wait, default_timelimit
	global MSG_TIME, W_HEIGHT, W_WIDTH, W_LBOR, W_RBOR, W_TBOR, W_BBOR, W_LRBOR, W_TBBOR, W_LPAD, W_RPAD, W_TPAD, W_BPAD, W_LRPAD, W_TBPAD
	global winthree
	#either create or destroy (toggle)
	if not(winthree):
		winthree = curses.newwin(W_HEIGHT-W_TBBOR-W_TBPAD-2, W_WIDTH-W_LRBOR-W_LRPAD, 4, 2)
		winthree.border(0,0,0,0,0,0,0,0)
		winthree.addstr(0, 2, 'SETUP', curses.A_REVERSE)
		winthree.addstr(2, 2, 'these are the current settings:', curses.A_NORMAL)


		winthree.addstr(4, 2, 'a) device:	%s' % DEV, curses.A_NORMAL)
		winthree.addstr(5, 2, 'b) baudrate:	%s' % BAUDRATE, curses.A_NORMAL)
		winthree.addstr(6, 2, 'c) timeout:	%s sec' % TIMELIMIT, curses.A_NORMAL)
		winthree.addstr(7, 2, 'd) display:	%s' % str(DISPLAY).replace(' ', ''), curses.A_NORMAL)
		winthree.addstr(8, 2, 'e) cells:	%s' % str(CELLS).replace(' ', '') , curses.A_NORMAL)
		winthree.refresh()

	else:
		winthree.clear()
		winthree.refresh()
		winthree = None




def main():

	global stdscr, winx, ctitle, format, CELLS, pid, die, alive, stop, stopped, pos, queue, header, data, files, signal, DISPLAY, TIMELIMIT, unit_timeout, prompt_wait, default_timelimit
	global MSG_TIME, W_HEIGHT, W_WIDTH, W_LBOR, W_RBOR, W_TBOR, W_BBOR, W_LRBOR, W_TBBOR, W_LPAD, W_RPAD, W_TPAD, W_BPAD, W_LRPAD, W_TBPAD

	#start the ncursing
	stdscr = curses.initscr()
	curses.noecho()
	curses.cbreak()
	stdscr.keypad(1)
	curses.curs_set(0)


	winx = curses.newwin(W_HEIGHT, W_WIDTH, 0, 0)
	winx.border(0,0,0,0,0,0,0,0)
	winx.addstr(0, 2, 'scintillation data collector', curses.A_REVERSE)


	x = 2
	for str in ['F1-HELP/INFO', 'F2-START/STOP', 'F3-SETUP', 'F4-QUIT']:
		winx.addstr(23, x, str, curses.A_REVERSE)
		x = x + 2 + len(str)

	winx.refresh()


	thread.start_new(clock, ()) #start the clock
	thread.start_new(messenger, ()) #start the messenger
	message(STR_WELCOME)

	"""
	import getopt
	tty = -1
	boot = False
	# parse command line options
	try:
		opts, args = getopt.getopt(sys.argv[1:], "fd", ["stdin", "device"])
	except getopt.error, msg:
		message(msg)
		#message("for help use --help")
		#sys.exit(2)

	# process arguments
	for arg in args:
		tty = str(abs(int(arg)))

	# process options
	for o, a in opts:
		if o in ("-f", "--stdin"):
			DEV = 'stdin'
			boot = True
		elif o in ("-d", "--device"):
			if tty > -1:
				DEV = '/dev/ttyS%s' % tty
	"""

	#get user input (wait for keypress)
	while 1:
		c = winx.getch() #stdscr.getch() doesn't work properly! why?

		if c == curses.KEY_F1 or c == ord('1'): #help (toggle)
			helpwindow()

		elif c in [curses.KEY_F2, ord('2')]: #start/stop toggle
			if stopped:
				thing = thread.start_new_thread(capture, ()) #start

			else:
				if stop: message(STR_ALREADY_TRY_STOP)
				else: finish()


		elif c in [curses.KEY_F3, ord('3')]: #setup
			setupwindow()

		elif c in [curses.KEY_F4, ord('4'), ord('q'), ord('Q')]: #quit
			finish()
			die = True #kill the clock&messenger
			limit = 0

			while alive > 0:
				if limit > 2*5 + 1:
					message(STR_KILL, 7)
					break #okay, i'm not going to wait forever!
				limit = limit + 1
				time.sleep(0.5) #let clock and/or messenger a chance to die

			break

		elif chr(c) in ['n', 'N', 'y', 'Y']: #send value to window prompt
			signal = c

		elif c == ord('g'): #start (go)
			if stopped:
				thing = thread.start_new_thread(capture, ()) #start capturing
			else: message(STR_ALREADY_START)

		elif c == ord('s'): #stop
			if stop: message(STR_ALREADY_TRY_STOP)
			else: finish()

		else:
			if len(STR_BAD_KEY) > 0: message(STR_BAD_KEY % c)


	restore() #fix terminal
	if len(queue) > pos: #there are more msg's in queue
		if (len(queue) - pos) == 1: print 'there was 1 message left to DISPLAY in the queue.\n'
		else: print 'there were %s messages left to DISPLAY in the queue.\n' % (len(queue) - pos)
		i = 1
		while len(queue) > pos:
			print '%s) %s (lv:%s)' % (i, queue[pos]['text'], queue[pos]['level'])
			pos = pos + 1
			i = i + 1


def restore():
	global stdscr, winx, ctitle, format, CELLS, pid, die, alive, stop, stopped, pos, queue, header, data, files, signal, DISPLAY, TIMELIMIT, unit_timeout, prompt_wait, default_timelimit
	global MSG_TIME, W_HEIGHT, W_WIDTH, W_LBOR, W_RBOR, W_TBOR, W_BBOR, W_LRBOR, W_TBBOR, W_LPAD, W_RPAD, W_TPAD, W_BPAD, W_LRPAD, W_TBPAD
	stdscr.keypad(0);
	curses.echo()
	curses.nocbreak();
	curses.endwin()


#run program

#try:
main()
"""
except:
	#curses.beep()
	#curses.flash()
	restore()
	print 'something crashed?\n'
	import traceback
	traceback.print_exc()           # Print the exception
        os.popen('kill -9 ' + str(pid)) #don't leave anyone (like a thread still going) alive


"""
