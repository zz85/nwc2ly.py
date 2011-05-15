import binascii, sys, zlib, traceback 
from ConfigParser import SafeConfigParser

shortcopyleft = """
nwc2ly - Converts NWC(v 1.75) to LY fileformat
Copyright (C) 2005  Joshua Koo (joshuakoo @ myrealbox.com)
and                 Hans de Rijck (hans @ octet.nl)

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""
## 
#
# 15 May 2011. imported from http://lily4jedit.svn.sourceforge.net/viewvc/lily4jedit/trunk/LilyPondTool/otherpatches/nwc2ly/nwc2ly.py?revision=457&content-type=text%2Fplain&pathrev=476
# Updated email
#
##
# most infomation obtained about the nwc format 
# is by using noteworthycomposer and the somewhat like the french cafe method
# (http://samba.org/ftp/tridge/misc/french_cafe.txt)
#
#
## 
# Revisions
# 0.1	07 april 2005 initial hex parsing;
# 0.2	13 april 2005 added multiple staff, keysig, dots, durations
# 0.3	14 april 2005 clef, key sig detection, absolute notes pitching
# 0.4   15 April 2005 Relative Pitchs, Durations, Accidentals, Stem Up/Down, Beam, Tie
# 0.5   16 April 2005 Bug fixes, Generate ly score , Write to file, Time Sig, Triplets, Experimental chords
# 0.6 	17 April 2005 Compressed NWC file Supported!
# 0.7 	19 April 2005 Version detection, Header 
#	20 April 2005 BUGS FiXes, small Syntax changes
#	21 April 2005 Still fixing aimlessly 
#	23 April 2005 Chords Improvement
#	24 April 2005 staccato, accent, tenuto. dynamics, midi detection (but unsupported)
# 0.8	24 April 2005 Experimental Lyrics Support
# 0.9	29 April 2005 Workround for \acciaccatura, simple Check full bar rest adjustment
# 1.0   10 July  2005 Hans de Rijck,
#			added dynamics, dynamic variance, tempo, tempo variance,
#			performance style, page layout properties
#			corrected barlines, lyrics, slurs, natural accidentals
#			using inifile for settings
#			limited support for NWC version 2.0
#	
## 
# TODO
# Proper syntax and structure for staffs, lyrics, layering
# version 1.7 Support
# nwc2ly in lilytool
# 
# Piano Staff
# Chords
# Midi Instruments
# Visability
# Lyrics
# Context Staff
# Staff layering / Merging
##
#
# BUGS text markups, chords
######
# 
# cd /cygdrive/c/development/nwc2ly
# $ python nwc2ly.py lvb7th1\ uncompressed.nwc test.ly > convert.log
#######

#################################
#           Options             #
#################################
    
cp = SafeConfigParser()
cp.read( 'C:\development\nwc2ly\hans version\nwc2ly.ini' )
#/cygdrive/C/development/nwc2ly/hans\ version/
debug			= int(cp.get('settings', 'debug'))
relativePitch		= int(cp.get('settings', 'relativePitch'))
relativeDuration	= int(cp.get('settings', 'relativeDuration'))
barLinesComments	= int(cp.get('settings', 'barLinesComments'))

insertBeaming		= int(cp.get('settings', 'insertBeaming'))
insertSteming		= int(cp.get('settings', 'insertSteming'))
insertText		= int(cp.get('settings', 'insertText'))

paperSize		= cp.get('settings', 'Papersize')
fillLast		= int(cp.get('settings', 'fillLast'))

LilyPondVersion		= cp.get('settings', 'LilyPondVersion')	

stdGrace		= cp.get('settings', 'stdGrace')	
accidentalStyle 	= cp.get('settings', 'accidentalStyle')	

#################################
#          /Options             #
#################################

global measureStart
global nwcversion

nwc2lyversion = '1.0'

##############

args =  len(sys.argv)
if args<2:
	print "Syntax: python nwc2ly.py nwcfile [lyfile]"
	sys.exit()
nwcfile = sys.argv[1]

if args<3:
	lyfile = ''
else:
	lyfile = sys.argv[2]



def getFileFormat(nwcData):
	global nwcversion
	#'[NoteWorthy ArtWare]'
	#'[NoteWorthy Composer]'
	nwcData.seek(0)
	company = readLn(nwcData)
	nwcData.seek(2,1) # pad
	product = readLn(nwcData)
	if debug: print "product: ", product
	#version = readLn(nwcData)
	
	version = nwcData.read(3)
	if debug: print " version: ", binascii.hexlify(version) 
	huh = nwcData.read(1)
	version = ord(version[0]) * 0.01 + ord(version[1])
	nwcversion = version
	print 'NWC file version', nwcversion, 'detected!'
	pad(nwcData,2) # times saved
	name1 = readLn(nwcData)
	name2 = readLn(nwcData)
	
	pad(nwcData,8)
	huh = nwcData.read(1)
	pad(nwcData,1)
	
def getFileInfo(nwcData):
	title = readLn(nwcData)
	author = readLn(nwcData)
	copyright1 = readLn(nwcData)
	copyright2 = readLn(nwcData)
	if nwcversion == 2.0 : whatsIt = readLn(nwcData)
	comments = readLn(nwcData)
	
	header = "\\header {"
	header += "\n\ttitle = \"%s\"" % title
	header += "\n\tcomposer = \"%s\"" % author
	header += "\n\tcopyright = \\markup \\teeny \"%s\"" % copyright1
	header += "\n\tfooter = \"%s\"" % copyright2
	header += "\n\t%%{ %s %%}" % comments
	header += "\n}"
		
	# TO ADD IN DEFAULT BLANK FIELDS TO KEY IN
	print 'title,author,copyright1,copyright2,comments: ', (title,author,copyright1,copyright2,comments)
	return header

# Page Setup
def getPageSetup(nwcData):
	# ??
	margins = getMargins(nwcData)
	#getContents(nwcData)
	#getOptions(nwcData)
	staffSize = getFonts(nwcData)
	barlineCount = 0
	return margins, staffSize
	
def getMargins(nwcData):
	global measureStart
	#readTill(nwcData,'\x01')	# not correct, should read 9 bytes (HdR)
	temp = nwcData.read(9)
	if debug : print "skipping ", binascii.hexlify(temp)
	measureStart = ord( nwcData.read(1) )
	pad(nwcData,1)
	# get string size 43
	margins = readLn(nwcData)
	print 'Start measure ', measureStart
	print 'margins ', margins
    #mirrorMargines
	#UOM
	return margins 

def getOptions(nwcData):
	# page numbering, from
	# title page info
	# extend last system
	# increase note spacing for larger note duration
	# staff size
	# staff labels (none, first systems, top systems, all systems
	# measure numbers none, plain, circled, boxed
	# measure start
	return

def getFonts(nwcData):
	# 12 Times
	#readTill(nwcData,'\xFF')	#not correct, should read 36 bytes (HdR)
	nwcData.read(36)
	n = nwcData.read(1)
	print "Staff size: ", ord(n)
	pad(nwcData,1)
	for i in range (12):
		# Font Name
		font = readLn (nwcData)
		
		# 00
		
		# Style 'Regular' 'Italic' 'Bold' 'Bold Italic'
		style = ord(nwcData.read(1)) & 3
		
		# Size
		size = ord(nwcData.read(1))
		
		## 00
		nwcData.seek(1,1)
		
		# Typeface
		# 00 Western, b1 Hebrew
		typeface = nwcData.read(1)
		
		if debug: print 'Font detected' , font, 'size',size, 'style ', style, ' typeface',typeface
		
	return ord(n)
		  
def findNoOfStaff(nwcData):
	# Infomation on Staffs \x08 00 00 FF 00 00 n
	data = 0;
	
	readTill(nwcData,'\xFF')
	if debug: print "Where am I? ", nwcData.tell()

	nwcData.read(2)
	
	layering = nwcData.read(1) # FF or 00
	
	noOfStaffs = ord(nwcData.read(1))
	nwcData.read(1)
	if debug: print noOfStaffs, " noOfStaffs found"
	return noOfStaffs

def findStaffInfo(nwcData):
	# Properties for Staff
		# General 
			# Name.
			# Group
			# Ending Bar
		# Visual
			# Verticle Upper Size
			# Verticle Lower Size
			# Style
			# Layer Next Staff
			# Color
		# Midi
			# Part Volume
			# Stereo Pan
			# Transposition
			# Muted
			# PlayBack Device
			# Playback Channel
		# Instrument
			# Patch Name
			# Patch List Type
			# Bank Select 
			# Controller0
			# Controller32
	# Staff Lyrics
		# LineCount
		# AlignSyllableRule
		# StaffPlacementAligment
		# StaffPlacementOffset
		# StaffPropertiesVerticleSizeUpper
		# StaffPropertiesVerticleSizeLower
		
	format = ''
	staffName = readLn(nwcData)
	format += "\\context Staff = %s " % staffName # or voice or lyrics 
	
	groupName = readLn(nwcData) # HOW TO ORGANISE THEM??
	
	endbar = ord(nwcData.read(1)) & 7 # mask all but last bits
	print 'end ',endbar
	endingBar = ending[endbar] #  10 --> OC for lyrics?  10000 1100
	
	muted = ord(nwcData.read(1)) & 1
	nwcData.read(1)
	
	channel = ord(nwcData.read(1)) + 1
	nwcData.read(9)
	
	stafftype = staffType[ord(nwcData.read(1))&3]
	nwcData.read(1)
	
	uppersize = 256 - ord(nwcData.read(1))  # - signed +1 )& 2^7-1 )
	readTill(nwcData,'\xFF')
	
	lowersize = ord(nwcData.read(1))
	ww = nwcData.read(1) 
	print '[uppersize,lowersize]',[uppersize,lowersize]
	
	noOfLines = ord(nwcData.read(1))
	print '[staffName,groupName,endingBar,stafftype,noOfLines]', [staffName,groupName,endingBar,stafftype,noOfLines]
	
	layer = ord(nwcData.read(1)) & 1
	
	# signed transposition
	# FF?
	
	partVolume = ord(nwcData.read(1))
	ord(nwcData.read(1))
	
	stereoPan = ord(nwcData.read(1))
	if nwcversion == 1.7:
		nwcData.read(2)
	else:
		nwcData.read(3)
	
	nwcData.read(2)
	#lyrics = ord(nwcData.read(1)) & 1
	lyrics = readInt(nwcData)
	noOfLyrics = readInt(nwcData)
	
	lyricsContent = ''
	if lyrics:
		lyricOptions = readInt(nwcData)
		nwcData.read(3)
		for i in range(noOfLyrics):
			print 'looping ',i, 'where', nwcData.tell(), 'NoOfLyrics:', noOfLyrics
			#lyricsContent  += '\\ \lyricmode { ' # lyrics
			lyricsContent = str( getLyrics(nwcData) ) #
			#lyricsContent  += '}'
		nwcData.read(1)
	
	nwcData.read(1)
	color = ord(nwcData.read(1)) & 3 #12
	
	noOfTokens = readInt(nwcData)
	print noOfTokens, " Tokens found", nwcData.tell()
	return staffName, endingBar, noOfTokens, format, lyricsContent

def pad(nwcData, length):
	nwcData.seek(length,1)

def readTill(nwcData, delimit):
	data = ''
	value = ''
	while data!=delimit:
		value += data
		data = nwcData.read(1)
		
	return value
	
def readLn(nwcData):
	return readTill (nwcData,'\x00')
	# reads until 00 is hit
	# od oa == \n

def readInt(nwcData):
	data = nwcData.read(2)
	no = ord(data[0])
	no += ord(data[1]) * 256
	return no


def getLyrics(nwcData):
	
	data = ''
	print 'reach'
	data = nwcData.read(1)
	if data == '': return
	blocks = ord( data )
	if blocks==4: blocks = 1
	if blocks==8: blocks = 2
	if blocks == 0: return 
	data = ''
	lyricsLen = readInt(nwcData)
	
	print 'blocks ',blocks, 'lyrics len', lyricsLen, 'at ', nwcData.tell()
	
	nwcData.read(1)
	for i in range (blocks):
		data += nwcData.read(1024)
	
	lyrics = data[1:lyricsLen-1]
				
	lyrics = lyrics.replace( "\x00", "_ " )

	print 'lyrics ', lyrics
	return lyrics
	
def getDuration(data):
	durationBit = ord(data[2]) & 7
	durationDotBit = ord(data[6]) 
	
	duration = durations[durationBit]
	absDuration = revDurations[durationBit]
	if (durationDotBit & 1<<2):
		durationDot = '.'
		absDuration += revDurations[durationBit + 1]
	elif (durationDotBit & 1):
		durationDot = '..'
		absDuration += revDurations[durationBit + 1] + revDurations[durationBit + 1]
	else :
		durationDot = ''
	return duration + durationDot

def getKey(data):
	data = binascii.hexlify(data)
	
	if (keysigs.has_key(data)):
		return '\key ' + keysigs[data]
	return '% unknown key'

def getLocation(data):
	offset = ord(data[8]);
	if offset > 127 :
		return 256-offset
	
	#next statement doesn't work for me	(HdR)	
	#if (ord(data[9])>>3 & 1):
	#	return -offset
	
	return -offset
	
	return offset

def getAccidental(data):
	data = ord(data)
	data = (data & 7 )
	return acdts[data]

def getDynVariance(data):
	data = ord(data)
	data = (data & 7 )
	return dynVariance[data]

def getPerfStyle(data):
	data = ord(data)
	temp = '_\\markup {\\small \\italic \\bold {' + perfStyle[data] + '}}'
	return temp

def getTempoVariance(data):
	data = ord(data)
	if data == 0 or data == 1 :
		temp = '\\' + tempoVariance[ data ]
	else:
		temp = '_\\markup {\\small \\italic \\bold {' + tempoVariance[data] + '}}'
	return temp

def getNote(data):
	
	# pitch
	pitch = getLocation(data)
	
	# get Accidentals
	accidental =  getAccidental(data[9])
	
	# get Relative Duration
	duration = getDuration(data)
	
	# check stems
	stem = ord(data[4])
	stem = (stem >> 4) & 3
	
	# check beam
	beam = ord(data[4]) & 3
	
	# triplets 
	triplet = triplets [ord(data[4])>>2 & 3 ]
	
	# check tie
	tie = ''
	if ord(data[6]) >> 4 & 1:
		tie = '~'
	
	staccato = (ord(data[6]) >> 1) & 1
	accent = (ord(data[6]) >> 5) & 1
	
	tenuto = (ord(data[7]) >> 2) & 1
	grace = (ord(data[7]) >> 5) & 1
	
	# check slur
	slur = slurs[ord(data[7]) & 3 ]
	#if debug: print "Slur ", ord(data[7]), slur
	
	#TODO should use a dictionary
	return (pitch, accidental, duration, stem, beam, triplet, slur, tie, grace, staccato, accent, tenuto)

def getRelativePitch(lastPitch, pitch):
	octave = ''
	diff = pitch - lastPitch
	if diff>3:
		for i in range((diff-4 + 7)/7):
			octave += "'"
		if octave == '':
			octave += "'"
	elif diff<-3:
		for i in range((-diff-4 + 7)/7):
			octave += ","
		if octave == '':
			octave += ","
	return octave
	
def durVal(duration):
	where = duration.find('.')
	
	if where>-1:
		durVal = 128/int (duration[:where])
		nextVal = durVal
		for i in range(len(duration)-where):
			nextVal = nextVal / 2
			durVal += nextVal
		
	else:
		durVal = 128/int (duration)
	return durVal
	
def processStaff(nwcData):
	keysigCount =0
	timesigCount=0
	noteCount=0
	restCount=0
	staffCount=0
	clefCount=0
	textCount=0	 
	tempoCount=0
	barlineCount = measureStart - 1
	dynamicCount = 0
	
	lastPitch = scale.index('c')
	lastDuration = 0
	lastClef = scale.index(clefs[0])  # index referenced to note of last clef
	lastStem = 0
	lastTimesig = 1
	
	lastKey = { 'c': '', #c 
	'd': '', 'e': '', 'f': '', 'g': '', 'a': '', 'b': '' }
	currentKey = lastKey.copy()
	
	data = 0
	token = 1
	
	result = ""
	result += "\n\t\\new Staff {\n\t" + "#(set-accidental-style '" + accidentalStyle + ") "
	lastChord = 0
	lastGrace = 0;
	lastSlur = ' ';
	
	(staffName, endingBar, noOfTokens, format, lyrics) = findStaffInfo(nwcData);
	if debug: print "staff info: name, endingbar, noOfTokens, format, lyrics-"
	if debug: print staffName, endingBar, noOfTokens, format, lyrics
	
	if relativePitch: 
		result+="\\relative c {"
	else :
		result+=" {"

	result+= '\n\n\t% Staff ' + str(staff) + '\t\t(' + staffName + ')\n\n\t'
	result+= '\\set Staff.instrument = #\"' + staffName + '\"\n\t'
	result+= '\\set Score.skipBars = ##t\n\n\t'

	#print "00112233445566778899\n"
	extra = ''
	dynamic = ''
	style = ''
	# the juice
	
	dualVoice = 0
	while data!="":
		
		token += 1
		if token==noOfTokens:
			result += "\\bar \"" + endingBar + "\"\n\t\t"
			
			if dualVoice == 1:	   # no beams and slurs with two voices
				result += "%Todo: check for slurs and beams in the bar above\n\t\t"
			dualVoice = 0
			
			result += "}\n\t"
			if lyrics!='':
				result += '\n\t\t\\addlyrics{ ' + lyrics + '}'
			result += "\n\t}\n\t"
			print "going next staff! %s" % nwcData.tell()
			break
		
		
		if nwcversion==1.7:
			nwcData.seek(2,1)
		
		data = nwcData.read(1)
		#print 'test', data
		
		# clef
		if data=='\x00':
			data = nwcData.read(6)
			clefCount += 1
			if debug: print binascii.hexlify(data), '  = clef ',
			
			key = ord(data[2]) & 3 	
			octave = ord(data[4]) & 3
			# print binascii.hexlify(data) , "CLEF? "
			lastClef = scale.index(clefs[key]) + octaves[octave]
			#TODO check for octave shifts _8
			#lastClef += clefShift[octave] # on ottava don't shift, just print 8va 
			if debug: print clefNames[key], clefOctave[octave]
			result += '\clef "' + clefNames[key] + clefOctave[octave]+ '"\n\t\t'
			
		# key signature
		elif data=='\x01':
			data = nwcData.read(12)
			keysigCount = keysigCount + 1
			if debug: print binascii.hexlify(data), '  = Key signature ',
			
			#
			flatBits = ord(data[2])
			sharpBits = ord(data[4])
			
			for note in lastKey.keys():
				noteInd = ['a','b','c','d','e','f','g'].index(note)
				if (flatBits >> noteInd & 1):
					lastKey[note] = 'es'
				elif (sharpBits >> noteInd & 1):
					lastKey[note] = 'is'
				else:
					lastKey[note] = ''
			
			currentKey = lastKey.copy()
			if debug: print getKey(data[1:5])
			result = result + getKey(data[1:5]) + "\n\t\t"
			
			#print "data", binascii.hexlify(data)
			#print "flat", binascii.hexlify(flatBits)
			#print "sharp", binascii.hexlify(data[4])
			#print getKey(data[1:5])
			
		
		# barline
		elif data=='\x02':
			data = nwcData.read(4)
			#if debug: print '  = Barline ', barlines[ ord(data[2]) ]
			#if debug: print binascii.hexlify(data)
			barlineCount += 1
			currentKey = lastKey.copy()
			
			if ( data[2] == '\x00' ):
				result += "|\n\t\t"
			else:
				result += "\\bar \"" + barlines[ ord(data[2]) ] + "\"\n\t\t"
			
			if dualVoice == 1:	   # no beams and slurs with two voices
				result += "%Todo: check for slurs and beams in the bar above\n\t\t"
			
			if (barlineCount % barLinesComments == 0):
				result += "\n\t\t% Bar " + str(barlineCount + 1) + "\n\t\t" 
				#print '.',
				print 'Bar ', barlineCount, ' completed,'
			
			dualVoice = 0
		# Repeat
		
		elif data=='\x03':
			if debug: print "Repeat",
			data = nwcData.read(4)
			if debug: print binascii.hexlify(data),
			if debug: print "  = repeat: ", ord( data[2] )
			result += "%Todo: place alternatives for \\repeat volta " + str(ord( data[2] )) + "\n\t\t"
		
		# Instrument Patch
		elif data=='\x04':
			if debug: print "Instrument Patch",
			data = nwcData.read(10)
			if debug: print binascii.hexlify(data)
			#readLn(nwcData)
			#readLn(nwcData)
			#readLn(nwcData)
	
		# timesig
		elif data=='\x05':
			data = nwcData.read(8)
			if debug: print binascii.hexlify(data),
			timesigCount = timesigCount + 1	
			beats = ord(data[2])
			beatValues = [ 1, 2, 4, 8 ,6, 32 ]
			beatValue = beatValues[ord(data[4])]
			timesig = str(beats) + "/"  + str(beatValue)
			if debug: print '  = Timesig', timesig
			lastTimesig = timesigValues[timesig]
			result += "\\time " + timesig + " "
			
		# Tempo
		elif data=='\x06':
			if debug: print "Tempo  ",
			data = nwcData.read(7)
			if debug: print binascii.hexlify(data)
			tempo = readLn(nwcData)
		
			# byte 4 length, byte 6 note, 
			tempoNote = data[6]
			tempoDuration = ord(data[4])
			if debug: print "duration ", tempoDuration
			
			if ( data[6] == '\x00' ):
				tempoNote = '8'
				tempoMultiply = int( tempoDuration * 2)
			elif ( data[6] == '\x01' ):
				tempoNote = '8.'
				tempoMultiply = int( tempoDuration / 0.75 )
			elif ( data[6] == '\x02' ):
				tempoNote = '4'
				tempoMultiply = tempoDuration
			elif ( data[6] == '\x03' ):
				tempoNote = '4.'
				tempoMultiply = int( tempoDuration / 1.5)
			elif ( data[6] == '\x04' ):
				tempoNote = '2'
				tempoMultiply = int( tempoDuration / 2)
			elif ( data[6] == '\x05' ):
				tempoNote = '2.'
				tempoMultiply = int( tempoDuration / 3)

			result += '\n\t\t\\tempo ' + tempoNote + '=' + str( tempoMultiply ) + ' '
			tempoCount = tempoCount + 1	
		
		# dynamics
		elif data=='\x07':
			dynamicCount = dynamicCount + 1
			data = nwcData.read(9)
			if debug: print binascii.hexlify(data),
			dynamic = dynamics[ ord(data[4]) & 7 ]
			if debug: print '  = Dynamic ' + dynamic
			
		# note
		elif data=='\x08':
			data = nwcData.read(10)
			noteCount = noteCount + 1
			
			if debug: print 'note  ', binascii.hexlify(data) , noteCount , nwcData.tell(),
			
			(pitch, accidental, duration, stem, beam, triplet, slur, tie, grace, staccato, accent, tenuto) = getNote(data)
			
			if debug: print pitch, accidental, duration, stem, beam, triplet, slur, tie, grace, staccato, accent, tenuto
			
			 
			articulate = ''
			if staccato: articulate+= '-.'
			if accent: articulate+= '->'
			if tenuto: articulate+= '--'
			
			beam = beams[beam]
			
			chordMatters = ''
			if lastChord>0 and beam==']' :
				if debug: print 'Chord ] ', durVal(duration), lastChord
				chordMatters = ' } >> '
				lastChord = 0
			elif lastChord>0:
				if debug: print 'Chord last ', durVal(duration), lastChord
				dur = durVal(duration)
				#lastChord = 1.0/((1.0 / lastChord) - (1.0/durVal(duration)))
				lastChord -= dur 
				
				if lastChord <= 0 :
					chordMatters = ' } >> '
					lastChord = 0
					
				
			
			if not insertBeaming: beam = ''
			
			# pitch
			pitch += lastClef
			note = scale[pitch]
			
			natural = ''
						
			# get Accidentals
			if ( accidental == '!' ) :		   # also do forced naturals
				natural = accidental
				accidental = ''
			
			if (accidental!='auto'):
				currentKey[note[0]] = accidental
				
			accidental = currentKey[note[0]]
			
			if (relativePitch):
				octave = getRelativePitch(lastPitch, pitch)
				lastPitch = pitch
			else:
				octave = note[1:]
			pitch = note[0] + accidental + octave
			
			# get Relative Duration
			if (relativeDuration):
				if (lastDuration==duration):
					duration = ''
				else:
					lastDuration = duration
			
			# check stems
			if insertSteming and (stem!= lastStem) :
				lastStem = stem
				stem = stems[stem]
			else :
				stem = ''
			
			# normal note
			if extra!='':
				extra = '-"' + extra + '"'
			
			if grace and not lastGrace: result += '\\' + stdGrace + " { "
			
			if nwcversion == 2.0:
				if ( slur == ' ' or slur == '' ) and lastSlur == '(' : 
					slur = ')'
					lastSlur = ' '
					if debug : print ' slur closed'
				elif slur == '(' and lastSlur == '(' : 
					slur = ' '
					lastSlur = '('
					if debug : print ' slur continued'
				elif slur == '(' and lastSlur == ' ' : 
					slur = '('
					lastSlur = '('
					if debug : print ' slur opened'
				       
			if dualVoice == 1:	   # no beams and slurs with two voices
				beam = ''
				slur = ''

			if not grace and lastGrace: result += " } "
			result += triplet[0] + stem + pitch + natural + duration + articulate + dynamic + style + extra 
			result += slur + tie + beam + triplet[1]  +chordMatters  +  " "
			
			
			# reset
			lastGrace = grace
			extra = ''
			dynamic = ''
			style = ''
		# rest
		elif data=='\x09':
			data = nwcData.read(10)
			if debug: print 'rest  ', binascii.hexlify(data) , noteCount , nwcData.tell()
			(pitch, accidental, duration, stem, beam, triplet, slur, tie, grace, staccato, accent, tenuto) = getNote(data)
   			
			restCount = restCount + 1 
			
			# get Relative Duration
			duration = getDuration(data)
			if duration == '1':
				duration = lastTimesig
			if (relativeDuration):
				if (lastDuration==duration):
					duration = ''
				else:
					lastDuration = duration
					
			result = result + triplet[0] + 'r' + str(duration) + dynamic + triplet[1] + " "
			dynamic = ''

		#chord starting with a rest
		elif data == '\x12':
			data = nwcData.read(12)        # rest info now in data 	    
                        print binascii.hexlify(data), "Chord started with rest. Rest skipped for now"
			(pitch, accidental, duration, stem, beam, triplet, slur, tie, grace, staccato, accent, tenuto) = getNote(data)
			result += "\n\t\t\\mark \\markup  {r" + duration + "}\n\t\t%Todo: Above rest must be added to next chord\n\t\t"
			token -= 1	#doesn't count as token
			
		# chord
		elif data=='\x0A' : # or data=='\x12':
			if data == '\x0a' :
				data = nwcData.read(12)
			
			chordAmt = ord(data[10])
			chords = []
			chordDur = getDuration(data)
			#print 'duration',chordDur
						
                        print binascii.hexlify(data), "Chord ", chordDur, chordAmt
			#print 'no. of notes in chord' , chordAmt
			
			chord1 = []
			chord2 = []
			
			for i in range(chordAmt):
				# rest or note
				what = nwcData.read(1)
				data = nwcData.read(10)
				ha = getNote(data)

				noteCount = noteCount + 1
				if debug: print 'chord ', binascii.hexlify(data) , noteCount , nwcData.tell(),
				(pitch, accidental, duration, stem, beam, triplet, slur, tie, grace, staccato, accent, tenuto) = ha
				if debug: print pitch, accidental, duration, stem, beam, triplet, slur, tie, grace, staccato, accent, tenuto
				
				# add to list
				if ha[2] == chordDur or len(chord2) > 0:
					chord1.append( (pitch,accidental ) )
					if beam==0 or beam ==4 :
						lastChord = 0
				else : # 2 voices
					chord2.append(  (pitch,accidental, duration) )
					lastChord = durVal(duration)  
			
			if len(chord2)==0: # block chord
				result += triplet[0] + ' <'
				for i in range(len(chord1)):
					(pitch,accidental ) = chord1[i]
					pitch += lastClef
					note = scale[pitch]
					
					natural = ''
					
					# get Accidentals
					if ( accidental == '!' ) :		   # also do forced naturals
						natural = accidental
						accidental = ''
					
					if (accidental!='auto'):
						currentKey[note[0]] = accidental
						
					accidental = currentKey[note[0]]
					
					if (relativePitch):
						octave = getRelativePitch(lastPitch, pitch)
						lastPitch = pitch
					else:
						octave = note[1:]
					result += note[0] + accidental + octave + natural + ' '
					
				if dualVoice == 1:	   # no beams and slurs with two voices
					slur = ''

				result += '>' + chordDur + slur  + triplet[1] + ' ' # added slur (HdR)
				lastPitch = chord1[0][0] + lastClef
			else: # 2 voices  Beware, this is experimental and not working good.
				dualVoice = 1
				result += ' << ' 
				for i in range(len(chord2)):
					(pitch,accidental,duration ) = chord2[i]
					pitch += lastClef
					note = scale[pitch]
					
					if ( accidental == '!' ) :		   # also do forced naturals
						natural = accidental
						accidental = ''
					
					if (accidental!='auto'):
						currentKey[note[0]] = accidental
						
					accidental = currentKey[note[0]]
					
					if (relativePitch):
						octave = getRelativePitch(lastPitch, pitch)
						lastPitch = pitch
					else:
						octave = note[1:]
					result += note[0] + accidental + octave + duration + ' '  #no slur, must be done manually
				
				result += " \\\\ {"
				
				for i in range(len(chord1)):
					(pitch,accidental ) = chord1[i]
					pitch += lastClef
					note = scale[pitch]
					
					if ( accidental == '!' ) :		   # also do forced naturals
						natural = accidental
						accidental = ''
					
					if (accidental!='auto'):
						currentKey[note[0]] = accidental
						
					accidental = currentKey[note[0]]
					
					if (relativePitch):
						octave = getRelativePitch(lastPitch, pitch)
						lastPitch = pitch
					else:
						octave = note[1:]
					result += note[0] + accidental + octave + chordDur + ' '   # no slur, must be done manually
				if lastChord >0 : lastChord = durVal(duration) - durVal(chordDur)
				if lastChord==0: result += ' } >> '
				# end 2 voices
			lastDuration = chordDur
			# check if duration / stem  / same 
				# < >duration ties,beam, slurs
		
		# Pedal
		elif data=='\x0b':
			data = data = nwcData.read(5)
			if data[4] == '\x01':
				style += '\\sustainDown'
			elif data[4] == '\x00':
				style += '\\sustainUp'
			if debug: print binascii.hexlify(data),
			if debug: print '  = Pedal, style: ', style
		
		# midi control instruction / MPC
		elif data=='\x0d':
			if debug: print 'midi control instruction',
			data = data = nwcData.read(36)
			if debug: print binascii.hexlify(data)
		
		# fermata / Breath mark
		elif data=='\x0e':
			data = nwcData.read(6)
			style += getTempoVariance( data[4] )
			if debug: print binascii.hexlify(data),
			if debug: print "  = tempo variance, style: ", style
		
		# Dynamic variance
		elif data=='\x0f':
			data = nwcData.read(5)
			style += getDynVariance( data[4] ) 
			if debug: print binascii.hexlify(data),
			if debug: print "  = Dynamic variance, style: ", style
	
		# Performance Style
		elif data=='\x10':
			data = nwcData.read(5)
			style += getPerfStyle( data[4] ) 
			if debug: print binascii.hexlify(data),
			if debug: print "  = Performance Style, style: ", style
		
		# text
		elif data=='\x11':
			textCount = textCount + 1
			data = nwcData.read(2) #pad
			textpos = nwcData.read(1)
			data = nwcData.read(2) #pad
			text = ''
			data = nwcData.read(1)
			while data!='\x00':
				text += data
				data = nwcData.read(1)
			
			#if text.isdigit() : # check numbers
			#	text = "-\\markup -\\number "+ text 
			#	#text = "-\\markup {\\number "+ text +"}"
			#else :
			#	text = '-"' + text + '"'
			
			if text == 'tr':
				style += '\\trill'
			else :				  
				if insertText :			  
					extra += ' ' + text
			
		
		# todo
		else :
			print "WARNING: Unrecognised token ",binascii.hexlify(data), " at #", nwcData.tell(), " at Token",  token
			
			
			
	# output converted file?
	print "\nStats"
	print keysigCount, " keysigCount found"
	print noteCount, " notes found"
	print staffCount, " staffCount found"
	print clefCount, " clefCount found"
	print barlineCount, " barlineCount found"
	print timesigCount, " timesigCount found"
	print textCount, " textCount found"
	print tempoCount, " tempoCount found"
	print dynamicCount, " dynamicCount found"
	print restCount, " restCount found"
	
	return result
	
# Variables
keysigs = {
'00000000' : 'c \major % or a \minor' ,
'00000020' : 'g \major % or e \minor' ,
'00000024': 'd \major % or b \minor' ,
'00000064' : 'a \major % or fis \minor' ,
'0000006c' : 'e \major % or cis \minor' ,
'0000006d' : 'b \major % or gis \minor' ,
'0000007d' : 'fis \major % or dis \minor' ,
'0000007f' : 'cis \major % or ais \minor' ,
'00020000' : 'f \major % or d \minor' ,
'00120000' : 'bes \major % or g \minor' ,
'00130000' : 'ees \major % or c \minor' ,
'001b0000' : 'aes \major % or f \minor' ,
'005b0000' : 'des \major % or bes \minor' ,
'005f0000' : 'ges \major % or ees \minor' ,
'007f0000' : 'ces \major % or a \minor'
}

acdts = ( 'is', 'es', '!' ,'isis', 'eses', 'auto'  ) 

dynVariance = ( '\\<',   # crescendo
				'\\>',   # decrescendo
				'\\>', 	 # diminuendo
				'\\rfz', # rinforzando
				'\\sfz'	 # sforzando
				)

perfStyle =   ( 'ad lib.',
				'animato',
				'cantabile',
				'con brio',
				'dolce',
				'espressivo',
				'grazioso',
				'legato',
				'maestoso',
				'marcato',
				'meno mosso',
				'poco a poco',
				'piu mosso',
				'semplice',
				'simile',
				'solo',
				'sostenuto',
				'sotto voce',
				'staccato',
				'subito',
				'tenuto',
				'tutti',
				'volta subito'
				)

clefs = { 0 : "b'",
          1 : "d",
          2 : "c'",
          3 : "a'",
        }

clefNames = { 0: 'treble',
          1: 'bass',
          2: 'alto',
          3: 'tenor',
        }
octaves = { 0: 0, 1:7, 2:-7 }
scale = [   # this list is taken from lilycomp
        "c,,,","d,,,","e,,,","f,,,","g,,,","a,,,","b,,,",
        "c,,","d,,","e,,","f,,","g,,","a,,","b,,",
        "c,","d,","e,","f,","g,","a,","b,",
        "c","d","e","f","g","a","b",
        "c'","d'","e'","f'","g'","a'","b'",
        "c''","d''","e''","f''","g''","a''","b''",
        "c'''","d'''","e'''","f'''","g'''","a'''","b'''",
        "c''''","d''''","e''''","f''''","g''''","a''''","b''''",
        "c'''''","d'''''","e'''''","f'''''","g'''''","a'''''","b'''''",
        ]

stems = [ '\stemNeutral ', '\stemUp ', '\stemDown ']

# what is slur  3? continuation of existing slur? (HdR)						   
slurs = [ '', '(' , ')', '' ]

tempoVariance = ['breathe',
		'fermata',
		'accel.',
		'allarg.',
		'rall.',
		'ritard.',
		'rit.',
		'rubato',
		'string.'
		 ]
dynamics = [    '\\ppp ',
		'\\pp ',
		'\\p ',
		'\\mp ',
		'\\mf ',
		'\\f ',
		'\f ',
		'\\fff '
		]
 
triplets = [ 
	('' , '' ),
	( '\\times 2/3 { ', '') ,
	('' , '' ),
	('' , ' }' ),
	]

durations    = ( '1','2','4','8','16','32','64' ) 
revDurations = (  64, 32, 16,  8,   4,   2,   1 ) 

barlines = (
     '|', # 'Single'
     '||', # 'Double'
     '.|', # SectionOpen
     '|.', # SectionClose
     '|:', # MasterRepeatOpen
     ':|', # MasterRepeatClose
     '|:', # LocalRepeatOpen
     ':|', # LocalRepeatClose
)

ending = (
'|.', # SectionClose
':|', # MasterRepeatClose
'|', # 'Single'
'||', # 'Double'
'' # Open hidden
)

staffType = (
'Standard' , # Standard
'Upper Grand Staff' , # Upper Grand Staff
'Lower Grand Staff' , # Lower Grand Staff
'Orchestra' , # Orchestra
)


beams = [ '', '[', '',']' ]


# end ' \bar "|."'

# Notation Properties
# extra accidental spacing
# extra note spacing
# muted
# no ledger lines
# slurdirection
# tiedirection
# lyricsyllable
# visability 
# show printed
# item color

#dynamics
# cmd = DynamicVariance
# Decrescendo \setTextCresc \<
# setTextCresc Crescendo \>  setHairpinCresc
# Dynamics stop '\! '
# style = ff pp

clefOctave = [ '' , '^8', '_8' , '' ]
clefShift = [0,7,-7, 0]


# '#(set-accidental-style '#39'modern-cautionary)'
#(ly:set-point-and-click 'line-column)
#(set-global-staff-size 20)

timesigValues = { 
	'4/4' : '1', '3/4' : '2.', '2/4' : '2', '1/4' : '1', '6/4' : '2.', '5/4' : 1,
	'1/8' : '8', '2/8' : '4', '3/8' : '4.', '6/8' : '2.',
	'4/8' : '2', '9/8' : '12', '12/8' : '1',
	'2/2' : '1', '4/2' : '0', '1/2' : '2', 
        }

print "python nwc2ly is running..."
try:

	nwcData = open( nwcfile,'rb')
	
	# check if its a readable nwc format
	# compressed - [NWZ]
	# uncompressed - [NoteWorthy ArtWare] [NoteWorthy Composer]
	format = nwcData.read(5)
	if format== '[NWZ]':
		nwcData.seek(1,1)
		print 'Compressed NWC detected!'
		print 'Dumping to uncompressed NWC format and attemping conversion soon...'
		uncompress = open ('uncompressed.nwc','wb')
		uncompress.write(zlib.decompress(nwcData.read()))
		uncompress.close()
		print 'Inflating done. Now opening new file...'
		nwcData.close()
		nwcData = open( 'uncompressed.nwc','rb')
		nwcData.seek(6)
	elif format!= '[Note':
		print 'Unknown format, please use an uncompress NWC format and try again.'  
		sys.exit()
	
	
	if debug: print "Getting file format"
	getFileFormat(nwcData)
	if debug: print "Getting file info"
	fileInfo = getFileInfo(nwcData)
	if debug: print "Getting page setup"
	(margins, staffSize) = getPageSetup(nwcData)
	
	#0.09850000 0.20094000 0.29944000 0.50037998
	#0123456789012345678901234567890123456789012345
	topMargin = margins[0:9]
	leftMargin = margins[11:20]
	rightMargin = margins[22:31]
	bottomMargin = margins[33:42]
	
	topMargin = round( float(topMargin), 2 )
	bottomMargin = round( float(bottomMargin), 2)
	leftMargin = round( float(leftMargin), 2 )
	rightMargin = round( float(rightMargin), 2 )
	if debug: print "top ", str(topMargin)
	if debug: print "bottom ", str(bottomMargin)
	if debug: print "left ", str(leftMargin)
	if debug: print "right ", str(rightMargin)
	
	resultFile = '%% Generated from python nwc2ly converter v%s by Joshua Koo (zz85nus@gmail.com)' % nwc2lyversion
	resultFile += '\n\\paper \n{\n'
	resultFile += '\t#(set-paper-size "' + paperSize + '")\n'
	resultFile += '\t#(set-global-staff-size ' + str(staffSize) + ')\n'
	resultFile += '\ttopmargin = ' + str(topMargin) + '\\in\n'
	resultFile += '\tleftmargin = ' + str(leftMargin) + '\\in\n'
	resultFile += '\trightmargin = ' + str(rightMargin) + '\\in\n'
	resultFile += '\tbottommargin = ' + str(bottomMargin) + '\\in\n'
	resultFile += '\traggedlastbottom = ##'
	if fillLast: 
		resultFile += 'f\n' 
	else: 
		resultFile += 't\n'
	resultFile += '}'
	resultFile += '\n\n\\version "' + LilyPondVersion + '"'
	resultFile += "\n"
	
   # START WORK
	resultFile+= fileInfo
	resultFile+= "\n\n\\score {"
	resultFile+= "\n\t<<\n\t\t"
	
    
	noOfStaffs = findNoOfStaff(nwcData);
	
	for staff in range(1,noOfStaffs+1):
		print "\n\nWorking on Staff", staff
		result = processStaff(nwcData)
		#print result
		resultFile += result
	
	resultFile+= "\n\t>>"
#	resultFile+= "\n\t\layout {}"
#	resultFile+= "\n\t\midi {}"
	resultFile+= "\n}"
	nwcData.close()
	
	if lyfile=='':
		print 'Dumping output file to screen'
		print resultFile
	else :
		write = open( lyfile ,'w')
		write.write (resultFile)
		write.close()

except IOError:
	print 'File does not exist or an IO error occurred'
except Exception, e: #KeyError
	print "Error while reading data at ", nwcData.tell() ,"\n"
	print 'Dumping whatever result first'
	print resultFile
	print Exception, e
	traceback.print_exc()

print
print
print "Please send all bugs and requests to zz85nus@gmail.com"
