import sys
import os
import struct
from ctypes import (CDLL, get_errno)
from ctypes.util import find_library
from socket import (
    socket,
    AF_BLUETOOTH,
    SOCK_RAW,
    BTPROTO_HCI,
    SOL_HCI,
    HCI_FILTER,
)
def dissect_hci_command(command):
	type = command[0]
	opcode = struct.unpack("<H", command[1:3])[0]
	length = command[3]
	data = command[4:]
	return (type,opcode,length,data)

def dissect_hci_event(event):
	type = event[0]
	code = event[1]
	length = event[2]
	data = event[3:]
	return (type,code,length,data)

def dissect_hci_event_command_complete(payload):
	number = payload[0]
	opcode = struct.unpack("<H", payload[1:3])[0]
	status = payload[3]
	data = payload[4:]
	return (number,opcode,status,data)

class HCISocket:
	def __init__(self,index=0):
		if isinstance(index,str) and "hci" in index:
			index = int(index.split("hci")[1])
		self.socket = socket(AF_BLUETOOTH, SOCK_RAW, BTPROTO_HCI)
		self.socket.bind((index,))

		# No filter
		hci_filter = struct.pack("IIIh2x", 0xffffffff, 0xffffffff, 0xffffffff, 0)
		self.socket.setsockopt(SOL_HCI, HCI_FILTER, hci_filter)

	def recv(self):
		message = self.socket.recv(1024)
		return message

	def send(self, data):
		self.socket.send(data)

	def send_command(self,data):
		_, command_opcode,_,_ = dissect_hci_command(data)
		self.send(data)
		while True:
			response = self.recv()
			_, event_code,_, payload = dissect_hci_event(response)
			if event_code == 0xe and dissect_hci_event_command_complete(payload)[1] == command_opcode:
 				return response

	def close(self):
		self.socket.close()

def listCompatibleHciInterfaces(allowedBoards=[(1521,0xFFFF)]):
	compatibleBoards=[]
	for i in range(10):
		try:
			socket = HCISocket(index=i)
			response = socket.send_command(bytes.fromhex("01011000"))
			if len(response) > 7 and response[6] == 0:
				manufacturer = struct.unpack("H",response[-4:-2])[0]
				subversion = struct.unpack("H",response[-2:])[0]
				if (manufacturer,subversion) in allowedBoards or (manufacturer,None) in allowedBoards:
					compatibleBoards.append("hci"+str(i))
			socket.close()
		except OSError:
			pass
	return compatibleBoards
