#! /usr/bin/env python
# -*- coding: utf-8 -*-

# zynq-bootgen
# Copyright (C) 2013  Paulo Henrique Silva <ph.silva@gmail.com>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# ug585-Zynq-7000-TRM (pp. 151)
# Fields						Header Byte Address Offset
# Reserved for Interrupts		0x000 - 0x01F
# Width Detection				0x020
# Image Identification			0x024
# Encryption Status				0x028
# User Defined					0x02C
# Source Offset					0x030
# Length of Image				0x034
# Reserved						0x038
# Start of Execution			0x03C
# Total Image Length			0x040
# Reserved						0x044
# Header Checksum				0x048
# Unused						0x04C - 0x09C
# Register Initialization		0x0A0 - 0x89C
# Unused						0x8A0 - 0x8BF
# FSBL Image					0x8C0

import struct
import sys

class Image:

	def __init__(self, filename):
		self.fp = open(filename, "rb")

	def readWords(self, n):
		return struct.unpack("%dI" % n, self.fp.read(4 * n))		

	def readWord(self):
		return self.readWords(1)[0]

	def readBigEndianString(self):
		s = ""
		while True:
			block = struct.unpack(">4s", self.fp.read(4))[0]
			if block == '\x00\x00\x00\x00':
				break
			s += block[::-1]

		return s

	def seekTo(self, offset):
		self.fp.seek(offset, 0)

class RBLHeader:

	def __init__(self, image):		
		self.image = image
		self.interrupts 		= self.image.readWords(8)
		self.width_detection 	= self.image.readWord()
		self.image_id			= self.image.readWord()
		self.encryption_status  = self.image.readWord()
		self.user_defined       = self.image.readWord()
		self.source_offset		= self.image.readWord()
		self.length_of_image	= self.image.readWord()
		self.reserved_1			= self.image.readWord()
		self.start_of_execution = self.image.readWord()
		self.total_image_length = self.image.readWord()
		self.reserved_2			= self.image.readWord()
		self.header_checksum	= self.image.readWord()
		self.image.seekTo(0x0a0)

		self.registers = []

		for i in range(256):
			self.registers.append((self.image.readWord(), self.image.readWord()))

	def __str__(self):
		s = ""
		s += "%s: %x %x %x %x %x %x %x %x\n" % ("Reserved for Interrupts", 
			self.interrupts[0], self.interrupts[1], self.interrupts[2], self.interrupts[3],
			self.interrupts[4], self.interrupts[5], self.interrupts[6], self.interrupts[7])
		s += "%s: %x\n" % ("Width Detection", self.width_detection)
		s += "%s: %x\n" % ("Image Identification", self.image_id)
		s += "%s: %x\n" % ("Encryption Status", self.encryption_status)
		s += "%s: %x\n" % ("User Defined", self.user_defined)
		s += "%s: %x\n" % ("Source Offset", self.source_offset)
		s += "%s: %x\n" % ("Length of Image", self.length_of_image)
		s += "%s: %x\n" % ("Start of Execution", self.start_of_execution)
		s += "%s: %x\n" % ("Total Image Length", self.total_image_length)
		s += "%s: %x\n" % ("Header Checksum", self.header_checksum)
		s += "%s:\n" % "Register Initialization:"
		for reg in self.registers:
			s += "\t%x = %x\n" % reg
		return s

class ImageHeaderTable:

	def __init__(self, image):		
		self.image = image
		self.image.seekTo(0x8c0) # spec say 0x8a0, but it is not true
		self.version 				   = self.image.readWord() # spec say it should be 0x01010000 but it is 0x10100000
		self.count_image_headers	   = self.image.readWord()
		self.offset_partition_header   = self.image.readWord() * 4
		self.offset_first_image_header = self.image.readWord() * 4

	def __str__(self):
		s = ""
		s += "%s: %x\n" % ("Version", self.version)
		s += "%s: %x\n" % ("Count Image Headers", self.count_image_headers)
		s += "%s: %x\n" % ("Offset Partition Header", self.offset_partition_header)
		s += "%s: %x\n" % ("Offset First Image Header", self.offset_first_image_header)
		return s

class ImageHeader:

	def __init__(self, image, offset):		
		self.image = image
		self.image.seekTo(offset)
		self.offset_next_image_header 		= self.image.readWord() * 4
		self.offset_first_partition_header	= self.image.readWord() * 4
		self.parition_count					= self.image.readWord()
		self.image_name_length				= self.image.readWord()
		self.image_name 					= self.image.readBigEndianString()

	def __str__(self):
		s = ""
		s += "%s: %x\n" % ("Offset next image header", self.offset_next_image_header)
		s += "%s: %x\n" % ("Offset first partition count", self.offset_first_partition_header)
		s += "%s: %x\n" % ("Parition count (not used, must be 0)", self.parition_count)
		s += "%s: %x\n" % ("Image name length (actual partition count)", self.image_name_length)
		s += "%s: %s\n" % ("Image name", self.image_name)
		return s		

if __name__ == "__main__":

	if len(sys.argv) < 2:
		print >> sys.stderr, "Usage: %s <boot.bin>" % sys.argv[0]
		sys.exit(1)

	img = Image(sys.argv[1])

	rbl_header = RBLHeader(img)
	image_header_table = ImageHeaderTable(img)

	print rbl_header
	print image_header_table

	next_header = image_header_table.offset_first_image_header

	while next_header != 0:
		image_header = ImageHeader(img, next_header)
		next_header = image_header.offset_next_image_header

		print image_header
