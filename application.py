import argparse
import socket
import struct
import time
from datetime import datetime

HEADER_FORMAT="!HHHH" # format for the packet head
HEADER_SIZE=8 # The size of the header
DATA_SIZE=992 # max size of the data in a packet
PAKKET_SIZE=HEADER_SIZE + DATA_SIZE # total packet size
TIMEOUT= 0.4 # timeout in seconds

# control-flags

SYN=0b0100 #syn-flag to start the connection
ACK=0b0010 # acknowledge-flag
FIN=0b1000 #finish flag to close a connection
res_flag = 0b0000


"""
Arguments:
seqNum-> (int) this is the sequence number of the packet. It is used to identify the sequence for the sent packets. Each packet gets their own 
seqNum.
ackNum-> (int) the is the acknowledgement. This is used to see which packet that last got received.
Flags-> (int )controlflag, is decides the packet's role in the connection for example SYN to start, FIN to terminate, and ACK 
for acknowlegdement.
rwnd: (int) This is the receiver window. It says how much space the receiver have available to receive packets within.
data: (bytes, optional) this is the content of the packet. and if not provided, its is empty (b''). 

Description: this function makes a packet, that can be sent over the internet via UDP.
The packet contains a header and data. The header is packed with struct.pack() to make a binary version, 
because the data to be sent over the internet needs to be packed in a certain way and contains information 
about the sequence number, acknowledgement number, flags, receive window size, and data. 

Return: 
bytes-> a byte-string representing the entire packet (with header and data).
"""

def make_packet(seqNum, ackNum, flags, rwnd, data=b''):
   #packs header
   #HEADER_FORMAT defines how to pack the 4 parameters
   #the result is a binary representation of the header that will be sent in the packet
   header=struct.pack(HEADER_FORMAT, seqNum, ackNum, flags, rwnd)
   # returns the complete packet by adding the data to the header
   # 'data' is an optional parameter, and is empty of not provided/specified.
   return header + data

"""
Arguments: 
packet (bytes): this is the received UDP-packet that will be divided into header and data. 
it is expected to be a type string consisiting of a header and data.

Description: this function takes an UDP-packet as an argument and divides it in two parts: a header and data
The header contains controlinformation as: sequence number and acknowledgement number ... that gets extracted with help from
struct.unpack()
The data is the rest of the packet and represents the content that gets transferred.
It then packs the header into four seperate values that can be used later on.

Return:
The function returns seqNum, ackNum, flags, rwnd, data

Error-handling:
It is expected that the input (packet) is always a valid byte-string with the wanted length (minimum HEADER_SIZE)
If the packet is shorter than expected, then an IndexError or struct.error could occur when tryinhg
to extract the header or using struct.unpack()
"""

def unpack_packet(packet):
   # extracts the 8 first bytes from the packet, that makes up the header
   # HEADER_SIZE is a constant defined as 8 bytes, just like the formate of HEADER_FORMAT
   header=packet[:HEADER_SIZE]
   #the rest og the packet (after the header) is the data, the content that we will use/save
   # uses the same format as make_packet to be qonsequent.
   data=packet[HEADER_SIZE:]
   seqNum, ackNum, flags, rwnd=struct.unpack(HEADER_FORMAT, header)
   #returns all the parts from the packet:
   return seqNum, ackNum, flags, rwnd, data


def server(ip, port, discard_seq):

   """
   Arguments:
   ip (str) and port (int): the IP adresse and port-number, that the server will be listening at.
   discard_seq (int): the sequence number on the packet that will be discarded onece (for testing)
   
   Description: 
   This function implements an UDP-server, that listens for incoming UDP-packets from the client.
   The function uses UDP-sockets for communication, and handles a 3-way handshake (SYN, SYN-ACK, ACK) to establish a connection
   Its starts with waiting for SYN-packet in order to establisg a conenction. It then received the file-data in multiple packets and 
   acknowledges them with ACK-packets, and ends with saving and calculating throughput. In addition there is a test-scenario
   where a packet is getting discarded for testing.
   
   Input/Output:
   Read UDP-packets from the socket.
   Writes the received file to "received_file.jpg"
   Writes out status messages to the terminal

   Return:
   None (the program terminates when the connection closes)

   Exception handling:
   Checks if the expected seq is received: If it’s not the expected packet, it then waits for the right one, 
   and if it’s the right packet- the server sends ack for that exact packet to client to confirm the delivery of the packet:


   """
   #creates an UDP-socket with IPv4-adressing (AF_INET) and uses SOCK_DGRAM for UDP
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

   #binds the socket to the specified ip-adresse and port to start listening after incoming packets
   s.bind((ip, port))
   
   # prints out message that the server is listening is now listening for incoming packets
   print(f"The server is currently listening on {ip}:{port}")
   
   #initialization of the variables that is needed to receive and process packets
   expected_seq=1 # expected seq number for the next packet, starts with one
   file_data=bytearray() # buffer to save the received file data
   discard_once=True # Flag to discrad one packet once for testing
   last_ack_sent=0
   
# waiting for syn-packet in order to start the connection
   while True:
       # awaits to receive a packet. 'PACKET_SIZE' is the maximal size on the received packet
       packet, addr = s.recvfrom(PAKKET_SIZE)
       seqNum, ackNum, flags, rwnd, data= unpack_packet(packet)
       
       #if the SYN-flag is set, it means the client is starting to start a connection
       if flags & SYN:
          print ("Yay, Syn-packet is received.")
          syn_ack=make_packet(0, 0 , SYN | ACK, 15)
          s.sendto(syn_ack, addr)
          print("Yay! The syn-ack packet is sent!")
        
        #If the ACK-flag is set, it confirms the SYN-ACK and completes 3 way handshake
        #The connection gets established
       elif flags & ACK:
         print("Ack packet received, connection established")
         break #breaks out of the loop when connection established
       
   #Start a timer to measure how long it takes to receive the file
   start_time= time.time()

# receive data file
   while True:
      #awaits for receiving a packet with the file data
      packet, addr = s.recvfrom(PAKKET_SIZE)
      seqNum, ackNum, flags, rwnd, data= unpack_packet(packet)
      timestamp=datetime.now().strftime('%H:%M:%S.%f')[:-3]

      # if the FIN-flag is set, then the filetransfer is completed
      if flags & FIN:
         print("FIN packet is received")
         fin_ack=make_packet(0, 0, FIN | ACK, 0)
         s.sendto(fin_ack, addr)
         print("FIN- ACK packet is sent")
         break # breaks out of the loop after the file transfer
      
   
      #if discard once is true and the seqience number matches with the discard seq
      #the packet gets discarded for testing
      if discard_once and seqNum == discard_seq:
         print(f"{timestamp} --Packet {seqNum} is discarded once for testing")
         discard_once=False #makes sure that packet only gets dicarded once
         continue
      
      #if the sequence number is as expected, the data gets inserted into the received file
      if seqNum == expected_seq:
         print(f"{timestamp} -- packet {seqNum} is received")
         file_data += data
         expected_seq += 1 #increased the expected seq for the next packet
      
      elif seqNum > expected_seq: 
         print(f"{timestamp} -- out-of-order packet {seqNum} is received") #out of order packet received, waiting for the correct one
         ack_packet=make_packet(0, expected_seq -1, ACK, 15)
         s.sendto(ack_packet, addr)
      
      else:
         #ignore
         pass

      
      ack_to_send=expected_seq -1
      #end an ACK-packet that confirms reception if the last and corret received packet
      if ack_to_send != last_ack_sent:
         ack_packet= make_packet(0, expected_seq - 1, ACK, 15)
         s.sendto (ack_packet, addr) # send the ack-packet to client
         print(f"{timestamp} -- sending ack for received {expected_seq -1}")
         last_ack_sent =ack_to_send

   #writes out the received filedata into a file: in this case its a jpg (picture)
   with open ("received_file.jpg", "wb") as f:
      f.write(file_data)

   # when all packets is received, the timer stops and calculates transfer speed
   end_time=time.time()
   total_time=end_time-start_time   

   # calculates the throughput (how fast the data got transferred) in Mbps
   throughput=(len(file_data)*8) / (total_time) / 1e6     
   print(f"Yay! Throughputen is calculated, it is..... {throughput:.2f} Mbps")

   # closes the connection after the file is received
   print("Connection is closing ...")
   s.close()

        
# client-code
def client(ip, port, file_name, window_size):
   """
   Arguments: 
   ip (str): The servers IP-adresse
   port (int): the servers port-number
   file_name (str): The file to be sent
   window_size (int): The size of the sliding window

   Description:
   This function starts a client that completes a 3 way handshaek to establish a connection.
   The function reads a file, divides it into packets, and sends these packets with sliding window
   It also receives ACK-packets, moves the window forward, and retransmits when timeout
   It then end the connection with FIN-packet

   Input/Output:
   Reads file from disc
   Sends and receives UDP-packets on the socket
   Writes out status messages 

   Return:
   None, the programme end after the connection closes


   Exception handling:
   Handles socket.timeout with retransmitting SYN packets if needed
   
   """
   #created an UDP-socket
   s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.settimeout(TIMEOUT) # sets timeout in order to be able to handle lost ack/packets
   addr= (ip, port) # combines IP and PORT to one adresse

   # three- way handshake: starts the connection with SYN
   syn= make_packet(0, 0, SYN, 0)
   s.sendto(syn, addr)
   print("SYN- packet is senttt!")

   while True:
    try:
         #awaits syn-ack packet from server
         packet, _= s.recvfrom(PAKKET_SIZE)
         seqNum, ackNum, flags, rwnd, data= unpack_packet(packet)

         #if both SYN and ACK is set, it means the server accepcted the establishment
         if flags & (SYN | ACK):
            print("SYN-ACK packet is received")
            #adjusts the window size based on the rwnd (the servers availability)
            window_size= max(1, min(window_size, rwnd))
            #sends an ack back to the sever to complete the handshake
            ack=make_packet(0, 0, ACK, 0)
            s.sendto(ack, addr)
            print("Ack packet is sent")
            print("Connection is established")
            break
    except socket.timeout:
       # if no answer, send the SYN again
       s.sendto(syn,addr)

# reads and divides the file that is getting sent
   with open(file_name, "rb") as f:
        file_data= f.read() # read the entire file in bytes
   
   packets= [] #a list for all the packets that is getting sent
   seqNum= 1 # starts the sequence num at 1
    
   # divides the file in appropriate bits, and packs each bit in a packet
   for i in range(0, len(file_data), DATA_SIZE):
      chunk= file_data[i:i+DATA_SIZE] # retrieves a bit of the file
      packets.append(make_packet(seqNum, 0, 0, 0,chunk)) # makes a packet
      seqNum += 1

   base = 1 # the first sequence num in the window
   next_seq= 1 # the next sequence num that will be sent
   totalpackets= len(packets)
   last_ack_received= 0 # to not get duplicated ack
      

   # Sending the file 
   while base <= totalpackets:
        # as long as we are within the window size and have not sent all the packets:
        while next_seq < base + window_size and next_seq <= totalpackets:
            s.sendto(packets[next_seq -1 ], addr)
            window_packets=list(range(base, min(base+window_size, totalpackets +1)))
            timestamp=datetime.now().strftime('%H:%M:%S.%f')[:-3]
            print(f"{timestamp} -- packet with seq {next_seq} is sent, sliding window= {{{', '.join(str(x) for x in window_packets)}}}")
            next_seq +=1

        try:
            # waiting for ACK from server
            packet, _ = s.recvfrom(PAKKET_SIZE)
            seqNum, ackNum, flags, rwnd, data= unpack_packet(packet)
            if flags & ACK:
               if ackNum > last_ack_received:
               #if ACK is received, the base gets moved forward
                   print(f"{time.strftime('%H:%M:%S')} -- ACK for packet = {ackNum} is received")
                   last_ack_received = ackNum
                   base= ackNum +1
        except socket.timeout:
            print(f"{timestamp} -- RTO occured")
            for i in range(base, next_seq):
               print(f"{timestamp} -- Retransmitting packet with seq = {i}")
               s.sendto(packets[i -1], addr)
            next_seq= base #restarst the sequence from the base again
            
   # teardown- closes the connection

   #makes and sends a FIN-packet to ask if the transaction is done
   fin= make_packet(0, 0, FIN, 0)
   s.sendto(fin, addr)
   print("FIN packet is sent")


   # waits for FIN-ACK from server to confirm that the connection can close
   while True:
      try:
         packet, _ = s.recvfrom(PAKKET_SIZE)
         seqNum, ackNum, flags, rwnd, data= unpack_packet(packet)
         if flags & (FIN | ACK):
            print("FIN-ACK packet is received. hoorayyy. Connection is closing...")
            break 
      except socket.timeout:
          #if no answer, the FIN gets sent again
          s.sendto(fin, addr)
          print("FIN packet is resent")
   

   # closes the socket and terminates
   s.close()

# main-function

def main():
   """
   Arguments:
   None (taken from commando line via argparse)

   Description:
   Parses the commando line arguments in order to start the client or server
   Makes sure (validates) that the needed arguments is gived (in terminal)
   Starts either the server og the client with the right parameters

   Return:
   None

   Exception handling:
   Writes out messages if some nessecary arguments is missing

   """
   parser = argparse.ArgumentParser()

   # Defining the wanted the command line arguments
   parser.add_argument('-s', '--server', action='store_true') # starts as server
   parser.add_argument('-c', '--client', action='store_true') # starts as client
   parser.add_argument('-i', '--ip', type=str, default='127.0.0.1') #IP-adresse
   parser.add_argument('-p', '--port', type=int, default=8088) #Port
   parser.add_argument('-f', '--file', type=str) # the file that is getting sent
   parser.add_argument('-w', '--window', type=int, default=3) #Sliding window-size
   parser.add_argument('-d', '--discard', type=int, default=99999) #The sequence number that vil get discarded once (testing)
   args= parser.parse_args()

   # Starts eiter the server of the client based on the arguments above^
   if args.server:
      server(args.ip, args.port, args.discard)
   elif args.client:
      if not args.file:
         print("Please specify a file using -f :)")
         return
        
      client(args.ip, args.port, args.file, args.window)
   else:
      print("Specify with eithre --server (-s) or --client (-c)")

# Only run the program if main-file.
if __name__== "__main__":
   
   main()
    
