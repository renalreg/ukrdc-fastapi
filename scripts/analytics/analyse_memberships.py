import json
import matplotlib.pyplot as plt

with open("./scripts/analytics/output/uids.json", "r") as f1:
    uid_email_map = json.load(f1)

with open("./scripts/analytics/output/events.json", "r") as f2:
    creation_events = json.load(f2)

# Basic counting

for uid, events in creation_events.items():
    friendly_id = "/".join(uid_email_map.get(uid))
    print(friendly_id)
    print(uid)
    print(len(events))

    events.sort()

    counts_per_day = {}

    for event in events:
        date = event.split("T")[0]
        if date not in counts_per_day:
            counts_per_day[date] = 0

        counts_per_day[date] += 1

    plt.figure()
    plt.scatter(list(counts_per_day.keys()), list(counts_per_day.values()))
    plt.title(friendly_id)

    plt.xlabel("Date")
    plt.xticks(rotation=90, fontsize=10)

    plt.ylabel("New memberships")

    plt.savefig(f"./scripts/analytics/output/plot/{uid}.png")

    plt.close()
