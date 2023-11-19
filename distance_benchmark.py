import sys
import random
import string
import serial
# import pandas as pd

from serialController import SerialController
import scp


def create_payload(byte_size: int) -> str:
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(byte_size))

def run_benchmark(serialCtl: SerialController, distance: float, payload_size: int, dest: str) -> None:
    print(f"Running benchmark with payload size: {payload_size}")

    # Let it run for a fixed time (20s?)

    # Send saturation traffic:
    # serialCtl._send_to_serial(scp.message(create_payload(payload_size), dest))
    # when "m[D]" received, sleep(0.01) and repeat

    # Read all received:
    # serialCtl._receive_from_serial()
    # To evaluate:
    #   data throughput: payload_size/time_between_ACK
    #   delay: time_between_ACK

    # provide also statistical information
    #   Create a plot with twin ax for thrp and delay, plot moving average and confidence interval
    #   Expected: Std dev is lower with lower delay bc more data


def main():
    Tx_addr = 'AA'
    Rx_addr = 'AB'

    if len(sys.argv) > 1:
        Tx = False
    else:
        Tx = True

    print("Starting Distance Benchmark\nSetup:")
    serialCtl = SerialController()
    ports = serialCtl.get_ports()
    match len(ports):
        case 0:
            print("No ports found! Aborting...")
            sys.exit()
        case 1:
            print(f"Found 1 port!\nUsing {ports[0]}")
            port = ports[0]
        case _:
            print(f"Found multiple ports, pls select by index:")
            [print(f"{i}: {p}") for i, p in enumerate(ports)]
            idx = int(input("Idx: "))
            port = ports[idx]
            print(f"Using {port}")

    serialCtl.ser = serial.Serial(port=port, baudrate=115200, timeout=0.1)
    # configure
    if Tx:
        serialCtl._send_to_serial(scp.set_address(Tx_addr))
    else:  # Rx
        serialCtl._send_to_serial(scp.set_address(Rx_addr))
    # options:
    # decrease channel busy threshold (Default: 20)
    # serialCtl._send_to_serial(scp.configure(0, 2, 20))
    # enable Forward Error Correction
    # serialCtl._send_to_serial(scp.configure(0, 1, 1))

    if not Tx:
        sys.exit()

    print("\nStaring benchmarks")
    while True:
        try:
            dist = float(input("New distance: "))
        except ValueError:
            print("Exiting...")
            sys.exit()
        for payload_size in [1, 100, 180]:
            run_benchmark(serialCtl, dist, payload_size, Rx_addr)


if __name__ == "__main__":
    main()
