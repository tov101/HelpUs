import socket
import struct
import threading
import time

HOST = '127.0.0.1'
PORT = 0x2101
ENCODING = 'ascii'


def not_used(item):
    assert item == item


class RCServer(threading.Thread):
    def __init__(self):
        super(RCServer, self).__init__()
        # Give a name to this thread
        self.name = 'HelpUs_RemoteServer'
        self.daemon = True

        # Init Socket
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.__socket.ioctl(socket.SIO_LOOPBACK_FAST_PATH, True)
        except Exception as don_t_care:
            not_used(don_t_care)

        # Control by Events
        self.__event_close = threading.Event()
        self.__event_send = threading.Event()
        self.__event_receive = threading.Event()

        # Data
        self.__received_data = None
        self.__send_data = None

    def close(self):
        self.__event_close.set()

    def send(self, message):
        # Put data into send_data
        self.__send_data = message
        # Set Event
        self.__event_send.set()

    def receive(self):
        # Wait Message to be received
        while self.__event_receive.is_set():
            time.sleep(0.1)
        if self.__received_data:
            data = self.__received_data
            self.__received_data = None
            return data
        return None

    def __send(self, connection):
        message = self.__send_data.encode(ENCODING)
        message = struct.pack('<I', len(message)) + message
        connection.sendall(message)

    @staticmethod
    def __receive(connection):
        # Get Length of Data
        data = bytearray()
        while len(data) < 4:
            new_bytes = connection.recv(4 - len(data))
            if not new_bytes:
                return None
            data.extend(new_bytes)
        # Unpack Length
        length = struct.unpack("<I", data)[0]

        # Receive until all message bytes are retrieved
        data = bytearray()
        while len(data) < length:
            new_bytes = connection.recv(length - len(data))
            if not new_bytes:
                return None
            data.extend(new_bytes)

        message = bytes(data).decode(ENCODING)
        return message

    def run(self):
        # Initialization Part
        self.__socket.bind((HOST, PORT))
        self.__socket.listen()
        while not self.__event_close.is_set():
            self.__event_receive.set()
            self.__event_send.clear()
            connection, addr = self.__socket.accept()
            with connection:
                while True:
                    # Receive
                    if self.__event_receive.is_set():
                        data = self.__receive(connection)
                        if not data:
                            break
                        self.__received_data = data
                        # Clear Receive Event -> Prepare to send response.
                        self.__event_receive.clear()

                    # Send if needed.
                    if self.__event_send.is_set():
                        self.__send(connection)
                        # Clear Send Event
                        self.__event_send.clear()
                        # Set Receive Event -> Allow Server to receive commands anytime
                        self.__event_receive.set()

                    time.sleep(0.01)
        self.__socket.close()


class RCClient:
    def __init__(self):
        self.__socket = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.__socket.ioctl(socket.SIO_LOOPBACK_FAST_PATH, True)
        except Exception as don_t_care:
            not_used(don_t_care)
        self.__socket.settimeout(1)
        self.__socket.connect((HOST, PORT))
        self.__socket.settimeout(None)
        self.__socket.setblocking(True)

    def ping(self):
        try:
            self.connect()
            self.close()
            return True
        except Exception as don_t_care:
            self.close()
            not_used(don_t_care)
            return False

    def close(self):
        self.__socket.close()
        self.__socket = None

    def send(self, message):
        message = message.encode(ENCODING)
        message = struct.pack('<I', len(message)) + message
        self.__socket.sendall(message)

    def receive(self):
        # Get Length of Data
        data = bytearray()
        while len(data) < 4:
            new_bytes = self.__socket.recv(4 - len(data))
            if not new_bytes:
                return None
            data.extend(new_bytes)
        # Unpack in order to get Length
        length = struct.unpack("<I", data)[0]

        # Receive until all message bytes are retrieved
        data = bytearray()
        while len(data) < length:
            new_bytes = self.__socket.recv(length - len(data))
            if not new_bytes:
                return None
            data.extend(new_bytes)

        message = bytes(data).decode(ENCODING)
        return message

    def exchange(self, message):
        self.send(message)
        return self.receive()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 2:
        x = RCServer()
        x.start()
        while True:
            print(x.receive())
            print(x.send(input()))
    else:
        x = RCClient()
        while not x.ping():
            time.sleep(0.1)
        x.connect()
        x.close()
        x.connect()
        x.close()
        x.connect()
        while True:
            print(x.exchange(input()))
