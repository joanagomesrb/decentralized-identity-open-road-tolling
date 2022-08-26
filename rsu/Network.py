
import logging
import os

class Network:
    
    def __init__(self):
        self.startNetwork()

    def startNetwork(self):
        logging.warning("creating ap")
        os.system('sudo kill create_ap') 
        os.system('sudo create_ap wlp4s0 enp2s0 RSU_AP 12345600 --daemon')
        logging.warning("RSU network RSU_AP is running.")

if __name__ == "__main__":
    
    networkInit = Network()
    networkInit.startNetwork()