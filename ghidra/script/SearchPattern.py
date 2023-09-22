# -*- coding: utf-8 -*-

# Search pattern
#@author 
#@category Search.InstructionPattern
#@keybinding 
#@menupath 
#@toolbar 


import json
import os

class Tools:
	def hexToBinary(self, hexa_str):
		"""
		Converts a hexadecimal string to binary string.

		:param hexa_str: Hexadecimal in string format.
		:type hexa_str: str

		:return: Binary string of the hexadecimal string.
		:rtype: str
		"""

		return bin(int(hexa_str, 16))[2:].zfill(len(hexa_str)*4)

	def levenshteinDistance(self, string1, string2):
		"""
		Calculate the levenshtein distance between two strings

		:param string1: The first string.
		:type string1: str
		:param string2: The second string.
		:type string2: str

		:return: Number of the levenshtein distance.
		:rtype: int
		"""

		m, n = len(string1), len(string2)
		dp = [[0] * (n + 1) for _ in range(m + 1)]

		for i in range(m + 1):
			dp[i][0] = i

		for j in range(n + 1):
			dp[0][j] = j

		for i in range(1, m + 1):
			for j in range(1, n + 1):
				cost = 0 if string1[i - 1] == string2[j - 1] else 1
				dp[i][j] = min(
					dp[i - 1][j] + 1,       # deletion
					dp[i][j - 1] + 1,       # insertion
					dp[i - 1][j - 1] + cost  # substitution
				)

		return dp[m][n]

	def customInstrucsDistance(self, instrucs, target_instrucs):
		"""
		Calculate the distance between two instructions with a custom malus points

		:param instrucs: Instructions to try.
		:type instrucs: list
		:param target_instrucs: Instructions to compare with (target pattern).
		:type target_instrucs: list

		:return: Number of the malus points.
		:rtype: int
		"""

		# Malus points
		malus = 0

		for i in range(len(target_instrucs)):
			if target_instrucs[i] != "null":
				target_instruc = target_instrucs[i].split(',')

				# Check mnemonic
				mnemonic = target_instruc[0]

				if instrucs[i].getMnemonicString() != mnemonic:
					malus = malus + 5

				# Check operands
				nbops1 = instrucs[i].getNumOperands()
				nbops2 = target_instruc[1]
				if nbops1 - int(nbops2) != 0:
					malus = malus + 10
				else:
					for k in range(nbops1):
						operandData2 = target_instruc[2+k].split(':')

						# Check operand type
						operandType1 = instrucs[i].getOperandType(k)
						operandType2 = (operandData2[0])[1:]

						if int(operandType1) - int(operandType2) != 0:
							malus = malus + 10

		return malus

	def customPcodeDistance(self, pcode, target_pcode):
		"""
		Calculate the distance between two pcode with a custom malus points

		:param pcode: Pcode to try.
		:type pcode: list.list
		:param target_pcode: Pcode to compare with (target pattern).
		:type target_pcode: list.list

		:return: Number of the malus points.
		:rtype: int
		"""

		malus = 0

		# Check Pcode
		ins = 0
		op = 0
		while ins < len(target_pcode) and ins < len(pcode):
			while op < len(target_pcode[ins]) and op < len(pcode[ins]):
				if target_pcode[ins][op] != "null" and pcode[ins][op] - int(target_pcode[ins][op]) != 0:
					malus = malus + 2
					if (2 in target_pcode[ins] and 3 in pcode[ins]) or (3 in target_pcode[ins] and 2 in pcode[ins]):
						malus = malus + 10
				op = op + 1
			ins = ins + 1
		
		return malus

	def customSimilarityPercentage(self, hexa, target_hexa, instrucs, target_instrucs, pcode, target_pcode):
		"""
		Calculate the mean between all of the different distance based on different metadata

		:param hexa: Hexadecimal to try.
		:type hexa: str
		:param target_hexa: Hexadecimal to compare with (target pattern).
		:type target_hexa: str
		:param instrucs: Instructions to try.
		:type instrucs: list
		:param target_instrucs: Instructions to compare with (target pattern).
		:type target_instrucs: list
		:param pcode: Pcode to try.
		:type pcode: list.list
		:param target_pcode: Pcode to compare with (target pattern).
		:type target_pcode: list.list

		:return: Mean of the distance.
		:rtype: int
		"""

		distanceInstrucAndPcode = self.customInstrucsDistance(instrucs, target_instrucs)
		distanceHexa = self.levenshteinDistance(hexa, target_hexa)
		distancePcode = self.customPcodeDistance(pcode, target_pcode)

		mean = abs(distanceInstrucAndPcode + distanceHexa + distancePcode)

		if mean < 50:
			return True, mean
		else:
			return False, 0

	def splitAddress(self, hexa_address):
		"""
		Split a hexadecimal string to an address with the offset.

		:param hexa_address: Hexadecimal address.
		:type hexa_address: str

		:return: Base address with the offset.
		:rtype: str, str
		"""

		base_address = hexa_address[:-3] + "000"
		offset = "0x" + hexa_address[-3:]

		return base_address, offset


class FunctionTargetInfo:
	def __init__(self, name, hexa, instruc, zeph_reg, pcode):
		self.name = name
		self.instruc = instruc
		self.hexa = hexa
		self.zeph_reg = zeph_reg
		self.pcode = pcode

	def getHexa(self):
		return self.hexa

	def getInstruc(self):
		return self.instruc

	def getName(self):
		return self.name

	def getZephReg(self):
		return self.zeph_reg

	def getPcode(self):
		return self.pcode


class SearchBased:
	def findFunctionByHexaAndInstrucAndPcode(self, target_hexa, target_instrucs, target_pcode, potential_addrs_funcs_after_regs, force):
		"""
		Split a hexadecimal string to an address with the offset.

		:param target_hexa: Hexadecimal target to compare with.
		:type target_hexa: str
		:param target_instrucs: Instructions targets to compare with.
		:type target_instrucs: list
		:param target_pcode: Pcode target to compare with.
		:type target_pcode: list.list
		:param potential_addrs_funcs_after_regs: Addresses functions to potential targets.
		:type potential_addrs_funcs_after_regs: list
		:param force: enter in the force mode
		:type force: bool

		:return: Triplet to the potential found function with the similarity result 
		:rtype: Function, int, Address
		"""

		# Separate the 2 cases
		if potential_addrs_funcs_after_regs == None:
			# Get only the functions
			BB = currentProgram.getListing().getFunctions(True)  # List of functions
		else:
			BB = potential_addrs_funcs_after_regs  # List of addresses

		similitudes = []
		# for each function
		for bloc in BB:
			if force == True:
				# we will get the same number of instructions than the target instructions
				# get the perfect similitude for these instructions for the function
				if potential_addrs_funcs_after_regs == None:
					similitude = self.getBestSimiFunc(bloc.getEntryPoint(), target_instrucs, target_hexa, target_pcode, None)
				else:
					similitude = self.getBestSimiFunc(bloc, target_instrucs, target_hexa, target_pcode, potential_addrs_funcs_after_regs)

			else:
				similitude = self.getSimiFunc(bloc, target_instrucs, target_hexa, target_pcode, potential_addrs_funcs_after_regs)

			if similitude[0] != None:
				similitudes.append(similitude)

		if len(similitudes) == 0:
			return None, 0, None
		else:
			# Havec the best candidates at the beginning of the list
			similitudes.sort(key=lambda x: x[1])

			if len(similitudes) > 2 and similitudes[0][1] != similitudes[1][1]:
				return similitudes[0]
			elif len(similitudes) <= 2:
				return similitudes[0]
			else:
				num = 0
				best = 0
				for s in similitudes:
					if num == 0:
						best = s[1]
						num = num + 1
					elif s[1] == best:
						num = num + 1

				if num > 3:
					return [num, similitudes[0:3]]
				else:
					return [num, similitudes[0:num]]

	def getPcodeMnemo(self, instruc, size_pcode):
		"""
		Get the mnemonics of the Pcode for the instruction.

		:param instruc: Instruction to work on
		:type instruc: Instruction
		:param size_pcode: Size of the array of the Pcode.
		:type size_pcode: int

		:return: Mnemonics of the Pcode of the instruction
		:rtype: list
		"""

		# for each instruc, we have each pcode (1 instruc can have multiple pcode to describe it)
		pcode_instrucs = []
		for k in range(size_pcode):
			pcode = []

			# each pcode, we get a list of constant field values for each mnemonic
			if instruc != None:
				for l in instruc.getPcode():
					pcode.append(l.getOpcode())
			
				pcode_instrucs.append(pcode)

				instruc = instruc.getNext()
			else:
				break

		return pcode_instrucs

	def getInstrucs(self, addr, size_instrucs):
		"""
		Get the following instructions beginning with an address.

		:param addr: Address as the entry point
		:type addr: Address
		:param size_instrucs: Size of the target instructions.
		:type size_instrucs: int

		:return: Intructions
		:rtype: list
		"""

		instrucs = []
		instrucs.append(currentProgram.getListing().getInstructionAt(addr))

		# Generate instructions to have the number of instructions than the target instructions
		for k in range(size_instrucs-1):
			if instrucs[k] != None:
				instrucs.append(instrucs[k].getNext())
			else:
				break
	
		return instrucs

	def getSimiFunc(self, bloc, target_instrucs, target_hexa, target_pcode, potential_addrs_funcs_after_regs):
		"""
		Get the similitude result of a function.
		
		:param bloc: Function to get similitude result 
		:type bloc: Function
		:param target_hexa: Hexadecimal target to compare with.
		:type target_hexa: str
		:param target_instrucs: Instructions targets to compare with.
		:type target_instrucs: list
		:param target_pcode: Pcode target to compare with.
		:type target_pcode: list.list
		:param potential_addrs_funcs_after_regs: Addresses functions to potential targets.
		:type potential_addrs_funcs_after_regs: list

		:return: Triplet to the potential found function with the similarity result 
		:rtype: Function, int, Address
		"""
		
		# Get the hexa and instruc of the current basic bloc
		if potential_addrs_funcs_after_regs == None:
			instrucs = self.getInstrucs(bloc.getEntryPoint(), len(target_instrucs))
			hexa = self.getHexaBasicBloc(bloc.getEntryPoint(), target_hexa)
			pcode = self.getPcodeMnemo(currentProgram.getListing().getInstructionAt(bloc.getEntryPoint()), len(target_pcode))
		else:
			instrucs = self.getInstrucs(bloc, len(target_instrucs))
			hexa = self.getHexaBasicBloc(bloc, target_hexa)
			pcode = self.getPcodeMnemo(currentProgram.getListing().getInstructionAt(bloc), len(target_pcode))

		if None in instrucs:
			return (None, 0, None)

		# Generate similitude for the target hexa and instructions
		sim, res_sim = Tools().customSimilarityPercentage(hexa, target_hexa, instrucs,target_instrucs, pcode, target_pcode)
		if sim:
			if potential_addrs_funcs_after_regs == None:
				return (bloc, res_sim, None)
			else:
				return (currentProgram.getListing().getFunctionContaining(bloc), res_sim, bloc)

		else:
			return (None, 0, None)
			
	def getBestSimiFunc(self, entry_point, target_instrucs, target_hexa, target_pcode, potential_addrs_funcs_after_regs):
		"""
		Get the similitude result of a function.
		
		:param entry_point: Address of the entry point of the function 
		:type entry_point: Address
		:param target_hexa: Hexadecimal target to compare with.
		:type target_hexa: str
		:param target_instrucs: Instructions targets to compare with.
		:type target_instrucs: list
		:param target_pcode: Pcode target to compare with.
		:type target_pcode: list.list
		:param potential_addrs_funcs_after_regs: Addresses functions to potential targets.
		:type potential_addrs_funcs_after_regs: list

		:return: Triplet to the potential found function with the similarity result 
		:rtype: Function, int, Address
		"""
		
		similitudes = []
		ins = currentProgram.getListing().getInstructionAt(entry_point)
		if ins == None:
			return None, 0, None

		func = currentProgram.getListing().getFunctionContaining(ins.getAddress())
		while ins != None and currentProgram.getListing().getFunctionContaining(ins.getAddress()) != None and currentProgram.getListing().getFunctionContaining(ins.getAddress()).getEntryPoint() == func.getEntryPoint():
			instrucs = []
			# Get the instrucs, hexa and pcode starting at the current ins
			instrucs = self.getInstrucs(ins.getAddress(), len(target_instrucs))
			hexa = self.getHexaBasicBloc(ins.getAddress(), target_hexa)
			pcode = self.getPcodeMnemo(currentProgram.getListing().getInstructionAt(ins.getAddress()), len(target_pcode))

			if None in instrucs:
				break

			# Generate similitude for the target hexa, instructions and pcode
			sim, res_sim = Tools().customSimilarityPercentage(hexa, target_hexa, instrucs, target_instrucs, pcode, target_pcode)
			if sim:
				if potential_addrs_funcs_after_regs == None:
					if res_sim == 0:
						return (func, res_sim, None)
					similitudes.append((func, res_sim, None))
				else:
					if res_sim == 0:
						return (currentProgram.getListing().getFunctionContaining(entry_point), res_sim, entry_point)
					similitudes.append((currentProgram.getListing().getFunctionContaining(entry_point), res_sim, entry_point))

			ins = ins.getNext()

		if len(similitudes) == 0:
			return None, 0, None
		else:
			similitudes.sort(key=lambda x: x[1])

		return similitudes[0]

	def getHexaBasicBloc(self, addr, target_hexa):
		"""
		Get the following hexa beginning with an address.

		:param addr: Address as the entry point
		:type addr: Address
		:param target_hexa: The target hexa.
		:type target_hexa: str

		:return: Hexadecimals
		:rtype: str
		"""

		# Get the Bytes of all of the instructions of the Function
		hexa_data = []
		k = 0  # each instruction
		l = 0  # length

		instruc = currentProgram.getListing().getInstructionAt(addr)
		size_hexa_data = len(target_hexa)

		while l < size_hexa_data and instruc != None:
			# Get bytes and convert it to the good format
			bytes = instruc.getBytes()
			hexa_data.append("".join([format(byte & 0xff, "02x") for byte in bytes]))

			instruc = instruc.getNext()
			l = l + len(hexa_data[k])
			k = k + 1

		hexa_data_final = "".join(hexa_data)

		return hexa_data_final

	def getData(self, function):
		"""
		Get the data used by a function.

		:param function: Function containing infos for the target function
		:type function: FunctionInfo

		:return: References of each data and their addresses
		:rtype: (list of Reference, list of Address)
		"""

		dataIterator = currentProgram.getListing().getData(True)
		complet_zeph_reg = function.getZephReg()
		base_addr, _ = Tools().splitAddress(complet_zeph_reg)

		ref_data = []  # List of references to data that we found
		addrs = []  # List of addr that we found

		for data in dataIterator:
			if data is not None and data.getDefaultValueRepresentation() == base_addr + "h":
				ref_data.append(data.getReferenceIteratorTo())
			elif data is not None and data.getDefaultValueRepresentation() == complet_zeph_reg + "h":
				for ref in data.getReferenceIteratorTo():
					addr = ref.getFromAddress()

					addrs.append(addr)

		return (ref_data, addrs)

	def getAddrsFuncsFromRefData(self, function, ref_data):
		"""
		Get the addresses from the Reference data

		:param function: Function containing infos for the target function
		:type function: FunctionInfo
		:param ref_data: Function containing infos for the target function
		:type ref_data: FunctionInfo

		:return: References of each data and their addresses
		:rtype: (list of Reference, list of Address)
		"""

		addrs = []  # List of func that we found
		_, offset = Tools().splitAddress(function.getZephReg())

		for refs in ref_data:
			for ref in refs:
				addr = ref.getFromAddress()
				func = currentProgram.getListing().getFunctionContaining(addr)
				instruc = currentProgram.getListing().getInstructionAt(addr)

				if func is not None and instruc is not None and instruc.getMnemonicString() == "ldr":
					register = instruc.getResultObjects()[0]
					instruc = instruc.getNext()

					while func.getBody().contains(instruc.getAddress()):
						if instruc.getMnemonicString() == "ldr.w" and self.checkInputObjects(instruc.getInputObjects(), register, offset):
							addrs.append(instruc.getAddress())

						instruc = instruc.getNext()
		return addrs

	def checkInputObjects(self, inputs_objs, register, offset):
		"""
		Check the register and the offset of inputs objects from an instruction

		:param inputs_objs: Inputs objects
		:type inputs_objs: list of Object
		:param register: Register used by the instruction
		:type register: Object
		:param offset: Offset to target
		:type offset: str

		:return: If the register and the offset is used by the current input objects from the instruction
		:rtype: bool
		"""

		if len(inputs_objs) == 2:
			if inputs_objs[0] == register and inputs_objs[1].toString() == offset:
				return True
			elif inputs_objs[0].toString() == offset and inputs_objs[1] == register:
				return True

		return False

	def run(self):
		# File path for the JSON table you want to use
		file_path = "tables/table_broadcom.json"
		current_directory = os.getcwd()
		absolute_path = os.path.join(current_directory, file_path)
		with open(absolute_path, 'r') as json_file:
			# Load JSON data from the file
			patterns = json.load(json_file)

		# THRESHOLD to put some functions in the force mode
		threshold = 10

		# Create all of the FunctionTargetInfo objects
		functions_to_target = []
		for pattern in patterns:
			functions_to_target.append(FunctionTargetInfo(pattern['func'], pattern['hexa'].replace(" ", ""), pattern['instr'].split(';'), pattern['regs'], [x.split(',') for x in pattern['pcode'].split(';')]))

		functions_to_target_retry = []
		force = False
		while 1:
			if force == True:
				print("FORCE MODE ACTIVATED ! (" + str(len(functions_to_target_retry)) + " functions left)")
				functions_to_target = functions_to_target_retry
			for func in functions_to_target:
				# Separate the 2 cases (have a register or not)
				if func.getZephReg() != "null":
					# Get all the potential funcs found by using the specific zephyr register
					ref_data, addrs_ref = self.getData(func)
					potential_addrs_funcs = addrs_ref + self.getAddrsFuncsFromRefData(func, ref_data)

					similitudes = self.findFunctionByHexaAndInstrucAndPcode(func.getHexa(), func.getInstruc(), func.getPcode(), potential_addrs_funcs, force)

				else:
					similitudes = self.findFunctionByHexaAndInstrucAndPcode(func.getHexa(), func.getInstruc(), func.getPcode(), None, force)

				if type(similitudes) != list:
					if similitudes[0] == None:
						if force == False:
							functions_to_target_retry.append(func)
							continue
						print("No \"" + func.getName() + "\" function found matching the potentials targets \n")
					else:
						if force == False and similitudes[1] > threshold:
							functions_to_target_retry.append(func)
							continue
						print("Function target found: " + similitudes[0].getName() + " (" + func.getName() + ") with a difference of " + str(similitudes[1]))
						if similitudes[2] == None:
							print("--> Entry Point: " + str(similitudes[0].getEntryPoint()) + "\n")
						else:
							print("--> Load zephyr register: " + str(similitudes[2]) + "\n")
				else:
					# If we found multiple candidates, we have also try in force mode
					if force == False:
						functions_to_target_retry.append(func)
					print("Functions target found for " + func.getName() + " with the same best difference " + str(similitudes[1][0][1]) + ":")
					print(str(similitudes[0]) + " candidates:")
					for fun in similitudes[1]:
						print(fun[0])
					print("")

			if force == False and len(functions_to_target_retry) != 0:
				threshold = 50
				force = True
			else:
				break

if __name__ == "__main__":
	SearchBased().run()
