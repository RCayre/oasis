# Assembler and Disassembler errors
class AssemblyFailure(Exception):
    pass

class DisassemblyFailure(Exception):
    pass

# Analyzer errors

class AddressNotFound(Exception):
    pass

class MultipleCandidateAddresses(Exception):
    pass
