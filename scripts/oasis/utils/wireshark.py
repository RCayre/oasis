import tempfile,os,subprocess
from oasis.utils import conf_parser
from scapy.all import PcapWriter

class WiresharkStream:
    def __init__(self, output=None):
        fifoName = next(tempfile._get_candidate_names())
        self.fifoFilename = "/tmp/"+fifoName+".pcap"
        self.output = output
        os.mkfifo(self.fifoFilename)
        self.writer, self.outputWriter = None, None
        self.startWireshark()

    def startWireshark(self):
        self.wiresharkProcess = subprocess.Popen([conf_parser.getWireshark(),"-k", "-i",self.fifoFilename])
        self.writer = PcapWriter(self.fifoFilename,sync=True)
        if self.output is not None:
            self.outputWriter = PcapWriter(self.output)

    def write(self, pkt):
        try:
            if self.writer is not None:
                self.writer.write(pkt)
            if self.outputWriter is not None:
                self.outputWriter.write(pkt)

        except BrokenPipeError:
            pass

    def __del__(self):
        self.wiresharkProcess.terminate()
        os.unlink(self.fifoFilename)
