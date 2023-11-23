import pandas as pd
import matplotlib.pyplot as plt

def create_plot(payload_size, data):
    fig, ax1 = plt.subplots()
    ax1.plot(data["dist"], data["avg_thrp"], color="blue", label="thrp")
    ax1.set_xlabel("distance [cm]")
    ax1.set_ylabel("thrp [B/s]")

    ax2 = ax1.twinx()
    ax2.plot(data["dist"], data["avg_delay"], color="red", label="delay")
    ax2.set_ylabel("delay [s]")

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc="upper left")

    plt.title(f"Plot thrp/delay, payload size: {payload_size} B")


if __name__ == "__main__":
    results = pd.read_csv("results.csv")
    payload_sizes = results["payload_size"].unique()
    for payload_size in payload_sizes:
        create_plot(payload_size, results[results["payload_size"] == payload_size])
    plt.show()
