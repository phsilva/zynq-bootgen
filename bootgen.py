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

class BinaryFile:

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

class BootROMHeader:

	def __init__(self, bin_file):		
		self.interrupts 		= bin_file.readWords(8)
		self.width_detection 	= bin_file.readWord()
		self.image_id			= bin_file.readWord()
		self.encryption_status  = bin_file.readWord()
		self.user_defined       = bin_file.readWord()
		self.source_offset		= bin_file.readWord()
		self.length_of_image	= bin_file.readWord()
		self.reserved_1			= bin_file.readWord()
		self.start_of_execution = bin_file.readWord()
		self.total_image_length = bin_file.readWord()
		self.reserved_2			= bin_file.readWord()
		self.header_checksum	= bin_file.readWord()
		bin_file.seekTo(0x0a0)

		self.registers = []

		for i in range(256):
			self.registers.append((bin_file.readWord(), bin_file.readWord()))

	def __str__(self):
		s = "<BootROMHeader>\n"
		s += "{:45}: {:#010x} {:#010x} {:#010x} {:#010x} {:#010x} {:#010x} {:#010x} {:#010x}\n".format("Reserved for Interrupts", 
			self.interrupts[0], self.interrupts[1], self.interrupts[2], self.interrupts[3],
			self.interrupts[4], self.interrupts[5], self.interrupts[6], self.interrupts[7])
		s += "{:45}: {:#010x}\n".format("Width Detection", self.width_detection)
		s += "{:45}: {:#010x}\n".format("Image Identification", self.image_id)
		s += "{:45}: {:#010x}\n".format("Encryption Status", self.encryption_status)
		s += "{:45}: {:#010x}\n".format("User Defined", self.user_defined)
		s += "{:45}: {:#010x}\n".format("Source Offset", self.source_offset)
		s += "{:45}: {:#010x}\n".format("Length of Image", self.length_of_image)
		s += "{:45}: {:#010x}\n".format("Start of Execution", self.start_of_execution)
		s += "{:45}: {:#010x}\n".format("Total Image Length", self.total_image_length)
		s += "{:45}: {:#010x}\n".format("Header Checksum", self.header_checksum)
		s += "{:45}\n".format("Register Initialization")
		for reg in self.registers:
			if reg == (0xffffffff, 0):
				s += "\t<no more registers>\n"
				break
			s += "\t{:#010x} = {:#010x}\n".format(reg)
		return s

class ImageHeaderTable:

	def __init__(self, bin_file):		
		bin_file.seekTo(0x8c0) # spec say 0x8a0, but it is not true

		try:
			self.version = bin_file.readWord()
			if self.version != 0x01010000:
				raise ValueError("This is not a ImageHeaderTable")

			self.count_image_headers	   = bin_file.readWord()
			self.offset_partition_header   = bin_file.readWord() * 4
			self.offset_first_image_header = bin_file.readWord() * 4
		except:
			self.version = 0 # no ImageHeaderTable found, just ignore the rest of the file
			self.count_image_headers	   = 0
			self.offset_partition_header   = 0
			self.offset_first_image_header = 0

	def __str__(self):
		s = "<ImageHeaderTable>\n"
		s += "{:45}: {:#010x}\n".format("Version", self.version)
		s += "{:45}: {:#010x}\n".format("Count Image Headers", self.count_image_headers)
		s += "{:45}: {:#010x}\n".format("Offset Partition Header", self.offset_partition_header)
		s += "{:45}: {:#010x}\n".format("Offset First Image Header", self.offset_first_image_header)
		return s

class ImageHeader:

	def __init__(self, bin_file, offset):		
		bin_file.seekTo(offset)
		self.offset_next_image_header 		= bin_file.readWord() * 4
		self.offset_first_partition_header	= bin_file.readWord() * 4
		self.parition_count					= bin_file.readWord()
		self.image_name_length				= bin_file.readWord()
		self.image_name 					= bin_file.readBigEndianString()

	def __str__(self):
		s = "<ImageHeader>\n"
		s += "{:45}: {:#010x}\n".format("Offset next image header", self.offset_next_image_header)
		s += "{:45}: {:#010x}\n".format("Offset first partition count", self.offset_first_partition_header)
		s += "{:45}: {:#010x}\n".format("Parition count (not used, must be 0)", self.parition_count)
		s += "{:45}: {:#010x}\n".format("Image name length (actual partition count)", self.image_name_length)
		s += "{:45}: {}\n".format("Image name", self.image_name)
		return s

class BootImage:

	def __init__(self, filename):
		self.bin_file = BinaryFile(filename)
		self.boot_rom_header = BootROMHeader(self.bin_file)

		self.image_header_table = ImageHeaderTable(self.bin_file)
		self.image_header = []

		next_header = self.image_header_table.offset_first_image_header

		while next_header != 0:
			header = ImageHeader(self.bin_file, next_header)
			self.image_header.append(header)

			next_header = header.offset_next_image_header

	def __str__(self):
		if self.image_header_table.version != 0:
			return "\n".join([str(self.boot_rom_header), str(self.image_header_table)] + [str(x) for x in self.image_header])
		else:
			return str(self.boot_rom_header)

if __name__ == "__main__":

	if len(sys.argv) < 2:
		print >> sys.stderr, "Usage: %s <boot.bin>" % sys.argv[0]
		sys.exit(1)

	boot_image = BootImage(sys.argv[1])
	print boot_image
