
MSG_TIME = 3
W_HEIGHT = 24
W_WIDTH = 80
#BORDERS
W_LBOR = 1 #left
W_RBOR = 1 #right
W_TBOR = 1 #top
W_BBOR = 1 #bottom
W_LRBOR = W_LBOR + W_RBOR #left+right
W_TBBOR = W_TBOR + W_BBOR #top+bottom
#PADDING
W_LPAD = 1
W_RPAD = 1
W_TPAD = 1
W_BPAD = 1

W_LRPAD = W_LPAD + W_RPAD
W_TBPAD = W_TPAD + W_BPAD


timelimit = 30 #sec (USER SHOULD SET THIS)
unit_timeout = 1 #sec


#this is the table that is hardcoded into the scintillator under: F8-COMPUTER OUTPUT
#DO NOT EDIT (unless your scintillator has something different shown here)

ctitle = [''] * 23 #declare empty list of correct length
ctitle[ 0] = 'CRLF'
ctitle[ 1] = 'P#'
ctitle[ 2] = 'PID'
ctitle[ 3] = 'S#'
ctitle[ 4] = 'TIME'
ctitle[ 5] = 'CPMA'
ctitle[ 6] = 'A:2S%'
ctitle[ 7] = 'A:%REF'
ctitle[ 8] = 'CPMB'
ctitle[ 9] = 'B:2S%'
ctitle[10] = 'B:%REF'
ctitle[11] = 'CPMC'
ctitle[12] = 'C:2S%'
ctitle[13] = 'C:%REF'
ctitle[14] = 'SIS'
ctitle[15] = 'DPM1'
ctitle[16] = 'DPM2'
ctitle[17] = 'ELTIME'
ctitle[18] = 'FLAG'
ctitle[19] = 'tSIE'
ctitle[20] = '%LUM'
ctitle[21] = 'A:%CV'
ctitle[22] = 'B:%CV'

format = [''] * 23 #declare empty list of correct length
format[ 0] = 'X'
format[ 1] = '?' * 80 #this is the: `P#' cell, at the moment we make it unusually large so that it's not chosen
format[ 2] = 'BXXX'
format[ 3] = 'BXXX'
format[ 4] = 'BXXX.XX'
format[ 5] = 'BXXXX.XX'
format[ 6] = 'BXX.XX'
format[ 7] = 'BXXX.XX'
format[ 8] = 'BXXXX.XX'
format[ 9] = 'BXX.XX'
format[10] = 'BXXX.XX'
format[11] = 'BXXXX.XX'
format[12] = 'BXX.XX'
format[13] = 'BXXX.XX'
format[14] = 'BXX.XXX'
format[15] = 'BXXXX.XX'
format[16] = 'BXXXX.XX'
format[17] = 'BXXXXXX'
format[18] = 'BXXXX'
format[19] = 'B.XXX'
format[20] = 'BXXX'
format[21] = 'BXXX.XX'
format[22] = 'BXXX.XX'



#this is the format seen under `Output Cells?' and can be changed based on your data collection preference.
#WARNING: the last element in this array must be 0

cells = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 0]

#these are the cells printed to the ncurses screen while data is coming in...
display = [3, 4, 5, 14, 18] #it should be validated to not be too long in calculated string length!!! (or ncurses will barf i think)

def int2bin(n, count=8):
    """returns the binary of integer n, using count number of digits"""
    return "".join([str((n >> y) & 1) for y in range(count-1, -1, -1)])
