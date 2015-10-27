#!/usr/bin/python
#
# Ths is a rudimentary implementation of packet reception using YARD Stick One
# with RfCat demonstrated in Rapid Radio Reversing presented at ToorCon 17
# (2015).
#
# usage from rfcat interactive shell:
#   %run sl.py
#   rxsl(d)

from rflib import *
import sys

# This validity check is only verifying certain bytes that are present in all
# packets.  It really should be followed up (or replaced) by a checksum
# verification.
def packet_valid(p):
	if ord(p[0]) != 0x6d:
		return False
	if ord(p[1]) != 0xb6:
		return False
	if ord(p[6]) != 0x6d:
		return False
	if ord(p[7]) != 0xb6:
		return False
	if (ord(p[29]) & 0xfc) != 0:
		return False
	return True

# This could probably be simpler and/or easier to read.  It extracts every
# third bit in order to decode the pulse width modulation (PWM).  The PWM
# implemented by StealthLock is well behaved in that the pulse durations and
# interval durations are all one or two times the length of a time unit and
# data bits are represented by a consistent number (3) of time units.  This is
# the time unit I have used in the RfCat symbol rate configuration, so a long
# pulse appears as symbols (1, 1, 0) and a short pulse appears as (1, 0, 0).
def pwm_decode(p):
	biginteger = 0
	for byte in p:
		biginteger <<= 8
		biginteger |= ord(byte)
	biginteger >>= 12
	out = 0
	for i in range(28, (len(p)*8-12)/3, 1):
		out <<= 1
		out |= ((biginteger & 1) ^ 1)
		biginteger >>=3
	return out

# checksum byte is 0xff minus 8-bit addition of previous bytes, like so:
# hex(0xff-(0x02+0x98+0x76+0xff+0xff)&0xff)

def rxsl(device):
	device.setFreq(314980000)
	device.setMdmModulation(MOD_ASK_OOK)
	device.setMdmDRate(2450)
	device.setPktPQT(0)
	device.setMdmSyncMode(2)
	device.setMdmSyncWord(0x06db)
	device.setMdmNumPreamble(0)
	device.setMaxPower()
	device.makePktFLEN(30)

	while not keystop():
		try:
			pkt, ts = device.RFrecv()
			if packet_valid(pkt):
				#print "Received:  %s" % pkt.encode('hex')
				print "0x%012x" % pwm_decode(pkt)
		except ChipconUsbTimeoutException:
			pass
	sys.stdin.read(1)
