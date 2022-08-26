
from BackOfficeUtils import BackOfficeUtils

import socket, json, asyncio, time

RSU_IP = 'localhost'
RSU_PORT = 5556 

class BackOffice:

    def __init__(self):
        self.bo_utils = BackOfficeUtils()

        self.open_pool()
        self.create_wallet_trust_anchor()
        cred_offer, cred_def = self.issue_credential()     

        print(cred_offer, cred_def)  

        self.send_to_rsu(cred_offer, cred_def)

    def open_pool(self):
        loop = asyncio.get_event_loop()
        task = loop.create_task(self.bo_utils.open_pool())
        loop.run_until_complete(task)
        loop.close()
        loop.stop()

    def create_wallet_trust_anchor(self):
        loop = asyncio.new_event_loop()
        task = loop.create_task(self.bo_utils.create_wallet_trust_anchor())
        loop.run_until_complete(task)
        loop.close()
        loop.stop()

    def issue_credential(self):
        loop = asyncio.new_event_loop()
        task = loop.create_task(self.bo_utils.issue_credential())
        cred_offer, cred_def = loop.run_until_complete(task)
        loop.close()
        loop.stop()

        return cred_offer, cred_def


    def send_to_rsu(self, msg, msg2):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        rsu_to_send = ("127.0.0.1", RSU_PORT)
        new_connection = False

        while True:
            try:
                raw_data = self.socket.recv(4096)
                new_connection = False
                data = raw_data.decode("utf-8")
                message_received = json.loads(data)
                
            except:    
                new_connection = True
                self.socket.connect(rsu_to_send)
                
                # = json.dumps(msg)
                #self.socket.send(send_data_as_string.encode("UTF-8"))

                # msg shouldn't be str!
                msg1 = {"type": "cred_offer", "info": msg}
                self.socket.send(str(msg1).encode("utf-8"))

                # ack = self.socket.recv(4096)
                

                #sendBytes = self.socket.sendto(send_data_as_string.encode("UTF-8"), rsu_to_send)

                # self.socket.settimeout(100)
                # recv_data, server = self.socket.recvfrom(4096)
                # self.print_log("DEBUG", "Received {!r} from {}".format(recv_data, server))

                # if(server == (RSU_IP, RSU_PORT)):
                #     decodedData = recv_data.decode()
                #     data1 = json.loads(decodedData)
                #     self.print_log("WARNING", "Received {}".format(data1))

                # recv ack
                
            if new_connection:
                pass
            else:
                if message_received["type"] == "ack":
                    # send msg2
                    send_data_as_string = json.dumps(msg2)
                    self.socket.send(send_data_as_string.encode("UTF-8"))
                elif message_received["type"] == "prover_cred_req":
                    #send cred to rsu
                    pass
                    


                

                
                
                
                # except socket.timeout as e:
                #     self.print_log("WARNING", "No response from server, closing socket.")

        

    def print_log(self, type="DEBUG", value_color="", value_noncolor=""):
        """
        Set the colors for prints.
        """
        HEADER = '\033[92m'
        ENDC = '\033[0m'
        if type == "ERROR" :
            HEADER = '\u001B[31m'
        if type == "WARNING" :
            HEADER = '\033[93m'
        if type == "DEBUG" :
            HEADER = '\033[92m'
        print(HEADER + value_color + ENDC + str(value_noncolor))

if __name__ == "__main__":
    
    try:
        bo_init = BackOffice()
    except KeyboardInterrupt:
        print("\n")
        try:
            print("Press CTRL-C again within 2 seconds to quit")
            time.sleep(2)
            sys.exit(2)
        except KeyboardInterrupt:
            print("CTRL-C pressed twice: quitting!")
            


        
