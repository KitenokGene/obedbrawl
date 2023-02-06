import socket
import argparse
import time
import os
import binascii
import json
import traceback

from threading import *
from Packets.Factory import *
from Logic.Device import Device


class Networking(Thread):
    def __init__(self, args):
        Thread.__init__(self)

        self.settings = json.load(open('Settings.json'))

        self.address = self.settings["Address"]
        self.port = self.settings["Port"]
        self.client = socket.socket()
        self.args = args

    def run(self):
        self.client.bind((self.address, self.port))

        print('Server is listening on {}:{}'.format(self.address, self.port))

        while True:
            self.client.listen(5)
            client, address = self.client.accept()

            print('New connection from {}'.format(address[0]))
            clientThread = ClientThread(client, self.args.debug).start()


class ClientThread(Thread):
    def __init__(self, client, debug):
        Thread.__init__(self)

        self.client = client
        self.device = Device(self.client)
        self.debug  = debug

    def recvall(self, size):
        data = []
        while size > 0:
            self.client.settimeout(5.0)
            s = self.client.recv(size)
            self.client.settimeout(None)
            if not s:
                raise EOFError
            data.append(s)
            size -= len(s)
        return b''.join(data)

    def run(self):
        while True:
            header   = self.client.recv(7)
            packetid = int.from_bytes(header[:2], 'big')
            length   = int.from_bytes(header[2:5], 'big')
            version  = int.from_bytes(header[5:], 'big')
            data     = self.recvall(length)

            if len(header) >= 7:
                if length == len(data):
                    print('[*] {} received'.format(packetid))

                    try:
                        decrypted = self.device.decrypt(data)
                        if packetid in availablePackets:

                            Message = availablePackets[packetid](decrypted, self.device)

                            Message.decode()
                            Message.process()

                        else:
                            if self.debug:
                                print('[*] {} not handled'.format(packetid))

                    except:
                        if self.debug:
                            print('[*] Error while decrypting / handling {}'.format(packetid))
                            traceback.print_exc()
                else:
                    print('[*] Incorrect Length for packet {} (header length: {}, data length: {})'.format(packetid, length, len(data)))
            else:
                if self.debug:
                    print('[*] Received an invalid packet from client')
                self.client.close()
