import re
import os
from pathlib import Path
from urllib.request import urlopen
import json

import matplotlib.pyplot as plt

BENCHMARK_CONTRACTS = ["WETH10", "BaseJumpRateModelV2"]


def read_md(commit_hash):
    stats_file = f"./stats/{commit_hash}.md"
    numbers = {}

    if not os.path.exists(stats_file):
        return numbers

    with open(stats_file) as stats:
        text = stats.read()

        for contract in BENCHMARK_CONTRACTS:
            handwritten = re.findall(rf"### {contract}:\n((?:\|.+\n)*)", text)[0].split(
                "\n"
            )[5:]

            warped = re.findall(rf"### {contract}_warp:\n((?:\|.+\n)*)", text)[0].split(
                "\n"
            )[5:]

            handwritten_dict = {
                steps.split("|")[1].strip(): int(steps.split("|")[2].strip())
                for steps in handwritten[:-1]
            }

            warped_dict = {
                steps.split("|")[1].strip(): int(steps.split("|")[2].strip())
                for steps in warped[:-1]
            }
            numbers[contract] = (handwritten_dict, warped_dict)
    return numbers


def get_data(commit_hashes):
    data = {contract: dict() for contract in BENCHMARK_CONTRACTS}

    for hash in commit_hashes:
        values = read_md(hash)

        if not values:  # Check if empty
            print(f"empty {hash}")
            continue

        for contract in BENCHMARK_CONTRACTS:
            for key in values[contract][0].keys():
                if key not in data[contract]:
                    data[contract][key] = [[], []]
                for i in range(2):
                    data[contract][key][i].append(values[contract][i][key])

    return data


def fetch_commits():
    commitsLink = "https://api.github.com/repos/NethermindEth/warp/commits"
    f = urlopen(commitsLink)
    commits = json.loads(f.readline())
    commit_hashes = [commit["sha"] for commit in commits]
    return commit_hashes[-1::-1]


if __name__ == "__main__":
    commit_hashes = fetch_commits()
    data = get_data(commit_hashes)
    Path("./images").mkdir(parents=True, exist_ok=True)

    with open("README.md", "w") as md_file:
        md_file.write(
            "# Warp Benchmark\n Tracking the progress of Warp, the Solidity to Cairo compiler.\n"
        )

        for contract in BENCHMARK_CONTRACTS:
            md_file.write(f"## {contract}\n")
            for function in data[contract]:
                md_file.write(f"### {function}\n")

                handwritten = data[contract][function][0]
                warped = data[contract][function][1]
                plt.plot(range(len(handwritten)), handwritten, label="Handwritten")
                plt.plot(range(len(warped)), warped, label="Warped")
                plt.legend(
                    loc="upper center",
                    bbox_to_anchor=(0.5, 1.05),
                    ncol=3,
                    fancybox=True,
                    shadow=True,
                )
                plt.savefig(f'./images/{contract}_{function.replace(" ","_")}.png')

                md_file.write(
                    f'![steps graph](./images/{contract}_{function.replace(" ","_")}.png)\n'
                )
                plt.clf()
