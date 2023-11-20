import sys
import random
import string
import serial
import time
import numpy as np

from serialController import SerialController
import scp


def create_payload(byte_size: int) -> str:
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(byte_size))

def run_benchmark(serialCtl: SerialController, port: str, distance: float, payload_size: int, dest: str) -> None:
    print(f"Running benchmark with payload size: {payload_size}")

    msg_done = []
    msg_ack = []

    # Let it run for a fixed time (20s?)
    run_time = 20  # s

    start_time = time.time()
    serialCtl._send_to_serial(scp.message(create_payload(payload_size), dest))
    while time.time() - start_time < run_time:
        data = scp.decode(serialCtl._receive_from_serial())
        if data is not None:
            if data[0] == 'm' and data[1][0] == 'D':
                msg_done.append(time.time() - start_time)
                time.sleep(0.01)
                serialCtl._send_to_serial(scp.message(create_payload(payload_size), dest))
            if data[0] == 'm' and data[1][0] == 'R' and data[1][1] == 'A':
                msg_ack.append(time.time() - start_time)

    if len(msg_ack) != 0:
        time_between_ACK = np.array(msg_ack[:1] + [j - i for i, j in zip(msg_ack[:-1], msg_ack[1:])])
        avg_delay = np.mean(time_between_ACK)
        delay_std = np.std(time_between_ACK, ddof=1)
        thrp = payload_size/time_between_ACK
        avg_thrp = np.mean(thrp)
        thrp_std = np.std(thrp, ddof=1)
        return avg_delay, delay_std, avg_thrp, thrp_std, len(msg_ack)

    # Send saturation traffic:
    # serialCtl._send_to_serial(scp.message(create_payload(payload_size), dest))
    # when "m[D]" received, sleep(0.01) and repeat

    # Read all received:
    # serialCtl._receive_from_serial()
    # To evaluate:
    #   data throughput: payload_size/time_between_ACK
    #   delay: time_between_ACK

    # provide also statistical information
    #   Create a plot with twin ax for thrp and delay, plot moving average and confidence interval (maybe there is a better way)
    #   Expected: Std dev is lower with lower delay bc more data (only true for std dev of avg)


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

    #serialCtl.ser.close()

    if not Tx:
        sys.exit()

    time.sleep(5)
    print("\nStaring benchmarks")
    while True:
        try:
            dist = float(input("New distance: "))
        except ValueError:
            print("Exiting...")
            sys.exit()
        for payload_size in [1, 100, 180]:
            results = run_benchmark(serialCtl, port, dist, payload_size, Rx_addr)
            print(f"D: {dist}, S: {payload_size}\n{results}")

            not_empty = True
            while not_empty:
                not_empty = serialCtl._receive_from_serial()
            time.sleep(5)


if __name__ == "__main__":
    main()
