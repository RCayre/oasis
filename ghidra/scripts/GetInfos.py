#TODO Get informations to complete the JSON table
#@author 
#@category Search.InstructionPattern
#@keybinding 
#@menupath 
#@toolbar 

from ghidra.program.model.lang import OperandType

# Put the address you want to get informations to complete the JSON table
addr = "00036292"

instruc = currentProgram.getListing().getInstructionAt(toAddr(addr))

#1
operandTypeList = []
#4
nboperands = instruc.getNumOperands()
#5
operandList = []
#6
mnemonic = instruc.getMnemonicString()

pcode_op = ""
for pcode in instruc.getPcode():
	p = pcode.getOpcode()
	if pcode_op == "":
		pcode_op = str(p)
	else:
		pcode_op = pcode_op + "," + str(p)
print(pcode_op)

for k in range(nboperands):
	#1
	operandTypeList.append(instruc.getOperandType(k))
	#5
	operandList.append(instruc.getOpObjects(k))

if nboperands == 3:
	print(mnemonic + "," + str(nboperands) + ",(" + str(operandTypeList[0]) + ":" + str(operandList[0][0]) + "),(" + str(operandTypeList[1]) + ":" + str(operandList[1][0]) + "),(" + str(operandTypeList[2]) + ":" + str(operandList[2][0]) + ")")
elif nboperands == 2:
	print(mnemonic + "," + str(nboperands) + ",(" + str(operandTypeList[0]) + ":" + str(operandList[0][0]) + "),(" + str(operandTypeList[1]) + ":" + str(operandList[1][0]) + ")")
elif nboperands == 1:
	print(mnemonic + "," + str(nboperands) + ",(" + str(operandTypeList[0]) + ":" + str(operandList[0][0]) + ")")
