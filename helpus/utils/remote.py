import socket
import threading
import time

HOST = '127.0.0.1'
PORT = 0x2101
ENCODING = 'utf8'


class RCServer(threading.Thread):
    def __init__(self):
        super(RCServer, self).__init__()
        # Give a name to this thread
        self.name = 'RCServer HelpUs'
        # Socket Init
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__connection = None
        # Control by Events
        self.__event_close = threading.Event()
        self.__event_send = threading.Event()
        self.__event_received = threading.Event()

        # Data
        self.received_data = None
        self.__send_data = None

    def close(self):
        self.__event_close.set()

    def send(self, message):
        # Put data into send_data
        self.__send_data = bytes(message, encoding=ENCODING)
        # Set Event
        self.__event_send.set()

    def __send(self):
        self.__connection.sendall(self.__send_data)
        self.__event_send.clear()

    def receive(self):
        if self.received_data:
            data = self.received_data.decode(encoding=ENCODING)
            self.received_data = None
            return data

    def run(self):
        # Initialization Part
        self.__socket.bind((HOST, PORT))
        self.__socket.listen()
        self.__connection, addr = self.__socket.accept()
        with self.__connection:
            # Loop Continuously
            while not self.__event_close.isSet():
                # Receive
                data = self.__connection.recv(1024)
                if not data:
                    break
                self.received_data = data
                # Send if needed.
                if self.__event_send.isSet():
                    self.__send()
        self.__socket.close()


class RCClient:
    def __init__(self):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.__socket.connect((HOST, PORT))

    def close(self):
        self.__socket.close()

    def send(self, message):
        self.__socket.send(bytes(message, encoding=ENCODING))

    def receive(self):
        data = self.__socket.recv(1024)
        if data:
            return data.decode(encoding=ENCODING)


if __name__ == '__main__':
    # RCServer().start()
    x = RCClient()
    x.connect()
    while True:
        x.send(input())
