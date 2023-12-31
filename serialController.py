import serial.tools.list_ports
import serial
from threading import Thread
from queue import Queue
from queue import Empty
from time import sleep

import scp


class SerialController:
    serialPort = "COM3"
    baudRate = 115200
    running = False
    ser = None

    def __init__(self) -> None:
        self.send_queue = Queue()
        self.receive_queue = Queue()

    def get_ports(self) -> list:
        ports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(ports):
            print("{}: {} [{}]".format(port, desc, hwid))
        return [p.device for p in ports]



    def start(self, serialPort: str, baudRate: int) -> None:
        self.serialPort = serialPort
        self.baudRate = baudRate
        self.running = True

        self.ser = serial.Serial(port=self.serialPort, baudrate=self.baudRate, timeout=0.1)

        self.thread = Thread(target=self._run)
        self.thread.start()

    def stop(self) -> None:
        self.running = False
        self.thread.join()

    def send(self, data: str) -> None:
        self.send_queue.put(data)

    def receive(self) -> str:
        try:
            return self.receive_queue.get(timeout=0.1)
        except Empty:
            return

    def _send_to_serial(self, data: str) -> None:
        #print(f"Sending {data}", end="")
        self.ser.write(str.encode(data))

    def _receive_from_serial(self) -> str:
        data = self.ser.readline().decode()
        if(data != "" and data != "\n"):
            #print(f"Received {data}", end="")
            return data.rstrip()
        
    def _run(self) -> None:
        sleep(2)
        # self._setup_device()
        while self.running:
            try:
                data = self.send_queue.get(timeout=0.1)
            except Empty:
                pass
            else:
                self._send_to_serial(data)
            try:
                data = self._receive_from_serial()
            except Empty:
                pass
            else:
                if(data != ""):
                    self.receive_queue.put(data)
            sleep(0.01)
