from iota import Iota
from iota import ProposedTransaction
from iota import Address
from iota import Tag
from iota import TryteString

import time
from regex._regex_core import String

class MyIota:
    
    def __init__(self):
        self.addresses = []
        self.api =""
        self.connect_to_node()

    def connect_to_node(self):
        """ 
        Connects to an IOTA node. 
        """
        self.print_log("DEBUG" , 'Connecting to node')

        seed = "JBN9ZRCOH9YRUGSWIQNZWAIFEZUBDUGTFPVRKXWPAUCEQQFS9NHPQLXCKZKRHVCCUZNF9CZZWKXRZVCWQ";
        self.api = Iota('http://iota.av.it.pt:14265', seed, local_pow=True)

        addr = self.create_addresses(10)

    def create_addresses(self, nr):
        """ 
        Generates nr IOTA addresses. 

        Parameters
        -----------
        nr: int
            number of addresses to be generated
        """
        self.print_log("DEBUG" , 'Generating IOTA addresses')
        
        i = 0
        while i < nr-1:
            self.addresses.append(Address.random(90))
            i +=1

        return self.addresses

    def get_address(self):
        """ 
        Get one IOTA address. 

        Returns
        -------
        addr: Address
            IOTA valid address
        """
        try:
            addr = self.addresses.pop(len(self.addresses)-1)
            return addr
        except IndexError:
            self.print_log("ERROR", "There is no more addresses left. Creating 10 more...")
            self.create_addresses(10)
            self.get_address()

    def print_log(self, type="DEBUG", value_color="", value_noncolor=""):
        """ 
        Set the colors for print.
        """
        HEADER = '\033[92m'
        ENDC = '\033[0m'
        if type == "ERROR" :
            HEADER = '\u001B[31m'
        if type == "WARNING" :
            HEADER = '\033[93m'
        if type == "DEBUG" :
            HEADER = '\033[92m'
        if type == "OK" :    
            HEADER = '\033[96m'
        print(HEADER + value_color + ENDC + str(value_noncolor))

if __name__ == "__main__":

    myIota = MyIota()
    #myIota.connect_to_node()
