#todo:
#make work in any size terminal (or a terminal > some min size), and also a terminal that resizes...
#help program to understand multiple passes to data collection... or even infinite...
#read the new timeout idea in comment in start of capture function

from settings import * #my settings
import thread, time, os, curses, sys
lock = thread.allocate_lock()

#validate settings.py file...
try: crlf = ctitle.index('CRLF')
except ValueError:
	print 'you have not defined a CRLF element in your ctitle array!'
	sys.exit()

if (cells[-1] != crlf) or (cells.count(crlf) > 1):
	print 'there must be only one occurrence of: CRLF in your cells array, and it must be the last element.'
	sys.exit()


stdscr = None

signal = 0 #prompt value

#global pid
pid = os.getpid()

#signals
#global die, alive
#global stop, stopped
die = False
alive = False
stop = False
stopped = True


#for message queue-ing
#global pos, queue
pos = 0
queue = []

#sub windows...
winone = None
wintwo = None
winthree = None

#data
header = []
data = []

#because i'm cool
def clock():
	global stdscr, winx, ctitle, format, cells, pid, die, alive, stop, stopped, pos, queue, header, data, signal, display, timelimit, unit_timeout
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
		#should we put a lock around this?
		output = time.strftime('%d/%m/%Y %H:%M:%S')
		lock.acquire()
		winx.addstr(0, W_WIDTH-2-len(output), output, curses.A_REVERSE)
		winx.refresh()
		lock.release()
		time.sleep(0.1) #wait 1 sec (has to be less than one sec...?)


def messenger():
	global stdscr, winx, ctitle, format, cells, pid, die, alive, stop, stopped, pos, queue, header, data, signal, display, timelimit, unit_timeout
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
	global stdscr, winx, ctitle, format, cells, pid, die, alive, stop, stopped, pos, queue, header, data, signal, display, timelimit, unit_timeout
	global MSG_TIME, W_HEIGHT, W_WIDTH, W_LBOR, W_RBOR, W_TBOR, W_BBOR, W_LRBOR, W_TBBOR, W_LPAD, W_RPAD, W_TPAD, W_BPAD, W_LRPAD, W_TBPAD
	dict = {'text':text, 'level':level, 'count':count}
	lock.acquire()
	queue.append(dict)
	lock.release()


############************figure out what to do for timeout code for this function... remember we might not have a full rack of vials, or we might have spaces!
def capture():
# what we could do is have a long timeout for the first vial, and once we get that vial data, we'll know the time interval for at least that rack, and then all we
#have to do is wait every mod 12? (every new rack) for a longer timeout, and then for all the in betweens we give it a max of interval found... note:
#we're not changing the serial timeout, we pick some useful small multiple, but the thing loops every timeout seconds, and we'll know how many empty readlines
#to accept before calling it a real timeout!
	global stdscr, winx, ctitle, format, cells, pid, die, alive, stop, stopped, pos, queue, header, data, signal, display, timelimit, unit_timeout
	global MSG_TIME, W_HEIGHT, W_WIDTH, W_LBOR, W_RBOR, W_TBOR, W_BBOR, W_LRBOR, W_TBBOR, W_LPAD, W_RPAD, W_TPAD, W_BPAD, W_LRPAD, W_TBPAD

	"""from the pyserial.sf.net homepage... i'm therefore assuming, that i could do this, and say i keep doing readline, but i get seven in a row, then i know it must be timing out seven times, because i won't normally get that from my serial port, and i can say end while loop. RIGHT? test it.
	Be carefully when using "readline".
	Do specify a timeout when opening the serial port otherwise it could block forever if no newline character is received.
	Also note that "readlines" only works with a timeout.
	"readlines" depends on having a timeout and interprets that as EOF (end of file).
	It raises an exception if the port is not opened correctly.
	"""


	stopped = False
	timeouts = 0

	header = []
	data = []
	again = True #for spectrum messages
	justended = False
	f = None #file object to be...
	p = -1 #protocol #
	td = time.strftime('%d%m%Y_%H%M%S') #start time
	top = '' #what does at top of .csv file
	for i in range(len(cells)-1): #we don't want the crlf on the end...
		top = top + ctitle[cells[i]]
		if i < len(cells) - 2:
			top = top + ','
	ix = 0 #iterations per serial opening... (how many protocols in this capture sequence, even duplicates)
	zix = 0 #how many loops... (debug)

	#ser = open('/dev/ttyS0', 'rb') #read, binary
	try:
		global DEV
		if DEV == 'stdin':
			ser = open('H.txt', 'r')

		else:
			import serial
			ser = serial.Serial(DEV, baudrate=9600, timeout=unit_timeout, parity=serial.PARITY_EVEN, bytesize=serial.SEVENBITS) # (baudrate 9600 is the max for lsc)


	except: #too bad this is broken and doesn't seem to actually catch the error!! grrr why!? or maybe it does?
		message('problem opening file/device...')
		stopped = True
		#stop = True
		return


	message('data capture started...')
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
			message('data capture stopped.')
			break


		line = ser.readline() #read a '\n' terminated line (times out in x sec)


		if line != '':
			timeouts = 0 #reset counter
			split = []

			#process...
			"""this program expects certain settings on the scintillator side, and makes assumptions based on them.
			without correct settings, the data might be parsed wrongly, and there might not be any way to warn the user.
			some assumptions are:

			rs232 output form:
			- last cell is CRLF (element 0) carriage return / line break
			"""


			where = line.find(',EOP')
			if where > 0:
#			if line[1:7] == ',EOP' + chr(13) + chr(10): #lsc prints this at the end of a protocol?

				#do any end of protocol processing... maybe export to usb?
				header = [] #get it ready to receive a new header...
				data = []
				if not(f == None):
					msg = ' ENDOFFILE'
					f.write(('#' + msg + '#'*(len(top)-len(msg)-1)) + '\n')
					f.close()
					justended = True #tell timeout thing that a protocol just ended...
					timeouts = ((timelimit/unit_timeout)+1) + 1 #let's not wait anymore for prompt...
				f = None
				p = -1
				message('protocol #: %s ended.' % int(line[0:where]))
				again = True #reset spectrum message

			elif line[0:2] == 'S,':
				#skips parsing of spectrum data at the moment :(
				#send a message...
				if again:
					message('spectrum data found!')
					again = False #but only once per protocol please

			else:
				split = line.split(',')

				#TODO: modify split... ie: add the 0 onto the beginning of .543


				# we need to identify if we have a header, and where it is.
				# current logic is to look where the QIP value is supposed to be...
 				# this can be changed if we see any anomalies.
				if (len(split) >= 4) and (split[3] in ['SIS', 'tSIE', 'tSIE\AEC']):
					if len(header) > 0:
						message('second header found!', 7) #MAKE THIS ONE CRITICAL! or something...
						#f_err = open('/tmp/f_err-%s.csv' % (td), 'a')
						#f_err.write(line + '\n')
						#f_err.close()

					#process this header variable into an array of text for each line to be printed... (example below)
					header = ['header: ', split[3], 'header obtained at: %s' % time.strftime('%d/%m/%Y %H:%M:%S')]
					datawindow()


				elif len(split) == len(cells)-1: # -1 b/c no CRLF in split data
					#regular data... do something with it...
					if f == None:

						try: p = ctitle.index('P#')
						except ValueError: p = -1

						try: p = cells.index(p) #which cell?
						except ValueError: p = -1

						if p >= 0: p = split[p]
						else:
							p = '~1'

						ix = ix + 1
						f = open('/tmp/lscdata-p%s-%s-%s.csv' % (p, td, ix), 'w')
						f.write(top + '\n')

					f.write(','.join(split))
					data.append(split)
					datawindow()

				elif line == chr(10): # '\n'
					if justended: #there seems to be a newline all by itself after an *,EOP (is it me or the lsc?)
						pass
					else: message('random newline found and ignored...')


				else:
					#if this keeps coming up, likely select cells does not between this program and scintillator
					#if you're sure it matches, or occasionally this pops up, let me know! we have a new type of row :(
					message('unrecognized row of data!', 7)
					f_err = open('/tmp/f_err-%s.csv' % (td), 'a')
					f_err.write('start@%s>\n' % zix)
					for Z in range(len(line)):
						f_err.write(str(ord(line[Z])) + '\n')
					f_err.write('<end@%s\n\n' % zix)
					f_err.close()



		else:
			if timeouts > ((timelimit/unit_timeout)+1):
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
				while signal == 0:

					time.sleep(1) #wait 3 sec
					waittime = waittime + 1
					if waittime > 60: signal = ord('y') #so that things can run o/n

					if signal in [ord('y'), ord('Y')]:
						if justended: message('awaiting new protocol...')
						else: message('extending timeout...')

						timeouts = 0
						break

					elif signal in [ord('n'), ord('N')]:
						if justended: message('timing out capture...')
						else: message('timeing out...')

						stop = True #if reaches timelimit, kill it?
						break

					lock.acquire()
					if waittime == 15: winprompt.addstr(4, 2, 'please enter y/n', curses.A_NORMAL)
					if waittime % 15 == 0: curses.beep()
					if waittime % 5 == 0: curses.flash()
					winprompt.refresh()
					lock.release()

				winprompt.clear()
				winprompt.refresh()
				winprompt = None


			else: timeouts = timeouts + 1
			#print this data to be informative...


#try and get the capture thread to shutdown...
def finish():
	global stdscr, winx, ctitle, format, cells, pid, die, alive, stop, stopped, pos, queue, header, data, signal, display, timelimit, unit_timeout
	global MSG_TIME, W_HEIGHT, W_WIDTH, W_LBOR, W_RBOR, W_TBOR, W_BBOR, W_LRBOR, W_TBBOR, W_LPAD, W_RPAD, W_TPAD, W_BPAD, W_LRPAD, W_TBPAD

	if not(stopped):
		message('trying to stop data capture...')
		stop = True
		signal = ord('n') #in case prompt is open...
		timer = 0
		while not(stopped): #wait for serial port to close
			if timer > 3*60 + 1:
				message('data capture killed forcefully.', 7, 1) #but how is this actually getting done? it doesn't! or maybe it just times out.
				break #okay, i'm not going to wait forever!
			timer = timer + 1
			time.sleep(1)

		message('data capture stopped')


def helpwindow():

	global stdscr, winx, ctitle, format, cells, pid, die, alive, stop, stopped, pos, queue, header, data, signal, display, timelimit, unit_timeout
	global MSG_TIME, W_HEIGHT, W_WIDTH, W_LBOR, W_RBOR, W_TBOR, W_BBOR, W_LRBOR, W_TBBOR, W_LPAD, W_RPAD, W_TPAD, W_BPAD, W_LRPAD, W_TBPAD
	global winone
	#either create or destroy (toggle)
	if not(winone):
		winone = curses.newwin(W_HEIGHT-W_TBBOR-W_TBPAD-2, W_WIDTH-W_LRBOR-W_LRPAD, 4, 2)
		winone.border(0,0,0,0,0,0,0,0)
		winone.addstr(0, 2, 'HELP', curses.A_REVERSE)
		winone.addstr(2, 2, 'inside help window', curses.A_NORMAL)
		winone.refresh()
	else:
		winone.clear()
		winone.refresh()
		winone = None


def datawindow():
	global stdscr, winx, ctitle, format, cells, pid, die, alive, stop, stopped, pos, queue, header, data, signal, display, timelimit, unit_timeout
	global MSG_TIME, W_HEIGHT, W_WIDTH, W_LBOR, W_RBOR, W_TBOR, W_BBOR, W_LRBOR, W_TBBOR, W_LPAD, W_RPAD, W_TPAD, W_BPAD, W_LRPAD, W_TBPAD


	#for debug:
	#header = ['header: ', '<this is a test>', '...']
	#data = ['aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'bbbbbbbbbbbbbbbbbbbbbbbb', 'cccccccccccccccccccccccccccccccc', 'dddddddddddddddddddddddddddddddd', 'eeeeeeeeeeeeeeeeeeeeee', 'ffffffffffffffffffffffffffffffffffff', 'gggggggggggggggggggggggggggggggggggg', 'hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh', 'iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii', 'jjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjj', 'kkkkkkkkkkkkkkkkkkkkkkkk', 'llllllllllllllllllllllllllllllll', 'mmmmmmmmmmmmmmmmmmmmmmmm', 'nnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn']
	#maxlen = W_WIDTH-4-2


	header_height = 0
	if len(header) > 0: #do we have a header?
		header_height = len(header)

	heading = ''
	for i in range(len(display)):
		if len(format[display[i]]) > len(ctitle[display[i]]):
			buf = len(format[display[i]]) - len(ctitle[display[i]])
		else:
			buf = 0
		heading = heading + ctitle[display[i]] + (' '*buf)
		if i < len(display) - 1:
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
		for j in range(len(display)):

			if display[j] in cells:
				str = data[i+delta][ cells.index(display[j]) ]
				#str = formatsomehow(str) #format the str to add the 0 in front of an empty decimal?
				if ( len(str) > len(format[display[j]]) ):
					row = row + str[0:len(format[display[j]])-1] + '#' #show that it doesn't fit by including all but last char and replacing that with a hash (#)

				else:
					if len(format[display[j]]) > len(str):
						buf = len(format[display[j]]) - len(str)
					else:
						buf = 0

					row = row + str + (' '*buf)

			else:
				row = row + '?' * len(format[display[j]]) #value doesn't exist in output cells


			if j < len(display) - 1:
				row = row + ' '


		wintwo.addstr(1+header_height+1+i, 2, row, curses.A_NORMAL)

	wintwo.refresh()


def setupwindow():

	global stdscr, winx, ctitle, format, cells, pid, die, alive, stop, stopped, pos, queue, header, data, signal, display, timelimit, unit_timeout
	global MSG_TIME, W_HEIGHT, W_WIDTH, W_LBOR, W_RBOR, W_TBOR, W_BBOR, W_LRBOR, W_TBBOR, W_LPAD, W_RPAD, W_TPAD, W_BPAD, W_LRPAD, W_TBPAD
	global winthree
	#either create or destroy (toggle)
	if not(winthree):
		winthree = curses.newwin(W_HEIGHT-W_TBBOR-W_TBPAD-2, W_WIDTH-W_LRBOR-W_LRPAD, 4, 2)
		winthree.border(0,0,0,0,0,0,0,0)
		winthree.addstr(0, 2, 'SETUP', curses.A_REVERSE)
		winthree.addstr(2, 2, 'inside setup window... these are some settings we should show', curses.A_NORMAL)
		winthree.addstr(4, 2, '1) timeout timelimit', curses.A_NORMAL)
		winthree.addstr(5, 2, '2) baudrate', curses.A_NORMAL)
		winthree.addstr(6, 2, '3) serial port device', curses.A_NORMAL)
		winthree.addstr(7, 2, '4) cells array', curses.A_NORMAL)
		winthree.addstr(8, 2, '5) display array', curses.A_NORMAL)
		winthree.refresh()
	else:
		winthree.clear()
		winthree.refresh()
		winthree = None




def main():

	global stdscr, winx, ctitle, format, cells, pid, die, alive, stop, stopped, pos, queue, header, data, signal, display, timelimit, unit_timeout
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

	#fix this up, maybe indent it on the screen... ? maybe make f1, f2, f3 buttons at the bottom?
	#winx.addstr(2, 2, 'welcome to the lsc data collection program...')
	#winx.addstr(4, 2, 'pick an option')
	#winx.addstr(6, 2, '1. verify settings')
	#winx.addstr(7, 2, '2. start data collection')
	#winx.addstr(8, 2, '3. do that thing!')
	#winx.addstr(10, 2, 'q. quit')

	x = 2
	for str in ['F1-HELP', 'F2-START/STOP', 'F3-SETUP', 'F4-QUIT']:
		winx.addstr(23, x, str, curses.A_REVERSE)
		x = x + 2 + len(str)

	winx.refresh()


	thread.start_new(clock, ()) #start the clock
	thread.start_new(messenger, ()) #start the messenger
	message('welcome to the lsc data collection program...')
	#message('have a nice umbrella...')
	#message('peanuts are for elephants')
	#message('okay bye!')

	#get user input (wait for keypress)
	while 1:
		c = winx.getch() #stdscr.getch() doesn't work properly! why?

		if c == curses.KEY_F1 or c == ord('1'): #help (toggle)
			helpwindow()

		elif c == curses.KEY_F2 or c == ord('2'): #start/stop toggle
			if stopped:
				thing = thread.start_new_thread(capture, ()) #start capturing

			else:
				if stop: message('already trying to stop data capture')
				else: finish()


		elif c == curses.KEY_F3 or c == ord('3'): #setup
			setupwindow()

		elif c == curses.KEY_F4 or c == ord('4') or c == ord('q'): #quit
			finish()
			die = True #kill the clock&messenger
			limit = 0

			while alive > 0:
				if limit > 2*5 + 1:
					message('threads being killed forcefully.', 7, 1)
					break #okay, i'm not going to wait forever!
				limit = limit + 1
				time.sleep(0.5) #let clock and/or messenger a chance to die

			break

		elif chr(c) in ['n', 'N', 'y', 'Y']: #send value to window prompt
			signal = c

		elif c == ord('d'): #window test
			datawindow()

		elif c == ord('g'): #start (go)
			if stopped:
				thing = thread.start_new_thread(capture, ()) #start capturing
			else: message('already in capture mode!')

		elif c == ord('s'): #stop
			if stop: message('already trying to stop data capture')
			else: finish()

		else: message('uncaught key: %s pressed.' % c)


	restore() #fix terminal
	if len(queue) > pos: #there are more msg's in queue
		if (len(queue) - pos) == 1: print 'there was 1 message left to display in the queue.\n'
		else: print 'there were %s messages left to display in the queue.\n' % (len(queue) - pos)
		#maybe we could format this in a nicer way?
		i = 1
		while len(queue) > pos:
			print '%s) %s (lv:%s)' % (i, queue[pos]['text'], queue[pos]['level'])
			pos = pos + 1
			i = i + 1


def restore():
	global stdscr, winx, ctitle, format, cells, pid, die, alive, stop, stopped, pos, queue, header, data, signal, display, timelimit, unit_timeout
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
