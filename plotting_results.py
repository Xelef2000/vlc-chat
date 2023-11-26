import pandas as pd
import matplotlib.pyplot as plt

def create_plot(payload_size, data):
    bar_width = 1.5

    fig, ax1 = plt.subplots(figsize=(8,3))
    ax1.bar(data["dist"] - bar_width*0.5, data["avg_thrp"], bar_width, color="blue", label="thrp")
    ax1.errorbar(data["dist"] - bar_width*0.5, data["avg_thrp"], yerr=data["thrp_std"], fmt='.', color='Black', elinewidth=1,capthick=1,errorevery=1, alpha=1, ms=3, capsize = 3)
    ax1.set_xlabel("distance [cm]")
    ax1.set_ylabel("thrp [B/s]")

    ax2 = ax1.twinx()
    ax2.bar(data["dist"] + bar_width*0.5, data["avg_delay"], bar_width, color="red", label="delay")
    ax2.errorbar(data["dist"] + bar_width*0.5, data["avg_delay"], yerr=data["delay_std"], fmt='.', color='Black', elinewidth=1,capthick=1,errorevery=1, alpha=1, ms=3, capsize = 3, label="1σ convidence interval")
    ax2.set_ylabel("delay [s]")

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc="center left")
    ax1.set_ylim(0)
    ax2.set_ylim(0)

    plt.title(f"Plot thrp/delay, payload size: {payload_size} B")


if __name__ == "__main__":
    results = pd.read_csv("results.csv")
    payload_sizes = results["payload_size"].unique()
    for payload_size in payload_sizes:
        create_plot(payload_size, results[results["payload_size"] == payload_size])
    plt.show()
