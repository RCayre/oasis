import struct

def switch_endianness(val):
	return struct.unpack(">I",struct.pack("I",val))[0]

def generateFunctionHookPatch(dependency, zone, name, address, function, instruction):
  return dependency+":"+zone+":"+name+":"+hex(address)+":"+function+":"+instruction+"\n"

def generateFunctionPointerPatch(dependency, zone, name, address, function):
  return dependency+":"+zone+":"+name+":"+hex(address)+":"+function+"\n"

def generateValuePatch(dependency, zone, name, address, value):
  return dependency+":"+zone+":"+name+":"+hex(address)+":"+"0x{:08x}".format(switch_endianness(value))+"\n"
