How to run application.py:

In order to run the code you need to add the simple-topo.py in your virtualbox
The simple-topo.py file, the application.py (with the server AND the client), the Photo.jpg. They all need to be in the same directory.

You will then need to open two terminals, h1 and h2. And do the following steps:

1. Start the topology with:
sudo python3 simple-topo.py

2. Use the command xterm, to open a h1 and h2. One for server and one for client. The server and the client can be executed with these commands:

Server: python3 application.py -s -i <ip_address_of_the_server> -p <port>
Client: python3 application.py -c  -f Photo.jpg -i <ip_address_of_the_server> -p <server_port> -w <window_size>

You may use 'ifconfig' to find the ip-adresse of the server.
-W is optional for how big of a window-size you want.
-d is used when discarding a spesific packet

example with window size AND discard
Server: python3 application.py -s -i 10.0.1.2 -p 8080 -d 8
Client: python3 application.py -c -i 10.0.1.2 -p 8080 -f Photo.jpg -w 5 


3. Then you start off with running the server on h2, and right after you run the client on h1.
