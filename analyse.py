import pandas as pd, glob, os
files = glob.glob("ds000164/sub-*/func/*events.tsv")
print(len(files), "file is found")

parts = []
for f in files:
    d = pd.read_csv(f, sep="\t")
    d["subject"] = f.split(os.sep)[1]
    parts.append(d)

df = pd.concat(parts , ignore_index=True)
print(df.columns.tolist())
print(df["subject"].nunique() , "participant")
print(df.groupby("subject").size().describe())   #number of trial per participant
print(df["condition"].value_counts())
print(df.describe())
print(df["correct"].value_counts(dropna=False))
print((df["response_time"] == 0).sum(), "tane response_time = 0")
print(df["response_time"].isna().sum(), "tane empty response_time")
print(df.groupby("condition")["response_time"].mean())

# fix typo
df["condition"] = df["condition"].str.replace("=", "", regex=False)

# only congruent and incongruent trials are kept
df = df[df["condition"].isin(["congruent", "incongruent"])]
n_start = len(df)

#only correct answers are kept
df = df[df["correct"] == "Y"]

# unanswered(0) and overly fast(<200ms) attempts are cleaned up
df = df[df["response_time"] >= 0.2]

# Outliers are removed on an individual basis(those more than 3 SD away from the mean)
g = df.groupby("subject")["response_time"]
mean = g.transform("mean")
sd = g.transform("std")
df = df[(df["response_time"] - mean).abs() <= 3 * sd]

print(f"Temizlik: {n_start} denemeden {len(df)} tanesi kaldı")

# Average response time (ms) per person, per condition
table = df.pivot_table(index="subject", columns="condition",
                       values="response_time", aggfunc="mean") * 1000

# Stroop cost = incongruent - congruent
table["stroop_cost_ms"] = table["incongruent"] - table["congruent"]

# Divide into three categories (bottom 25% / middle 50% / top 25%)
table["category"] = pd.qcut(table["stroop_cost_ms"],
                            q=[0, 0.25, 0.75, 1],
                            labels=["bottom", "middle", "top"])

print(table.round(1))
print(table["category"].value_counts())
table.to_csv("stroop_cost_analyse.csv")



from scipy import stats
import matplotlib.pyplot as plt

congruent = table["congruent"]
incongruent = table["incongruent"]
cost = table["stroop_cost_ms"]

# Descriptive statistics 
print(f"Congruent:   M = {congruent.mean():.1f} ms, SD = {congruent.std():.1f}")
print(f"Incongruent: M = {incongruent.mean():.1f} ms, SD = {incongruent.std():.1f}")
print(f"Stroop cost: M = {cost.mean():.1f} ms, SD = {cost.std():.1f}")

# Paired t-test 
t, p = stats.ttest_rel(incongruent, congruent)
dof = len(cost) - 1  # degrees of freedom = number of participants - 1
print(f"t({dof}) = {t:.2f}, p = {p:.2e}")

# Cohen's d 
d = cost.mean() / cost.std()
print(f"Cohen's d = {d:.2f}")
print((cost > 0).sum(), "of", len(cost), "participants have a positive Stroop cost")

# Plots
fig, axes = plt.subplots(1, 2, figsize=(11, 4))

# Plot 1: distribution of Stroop costs
axes[0].hist(cost, bins=8, edgecolor="black")
axes[0].axvline(cost.mean(), color="red", linestyle="--", label="Mean")
axes[0].set_xlabel("Stroop cost (ms)")
axes[0].set_ylabel("Number of participants")
axes[0].set_title("Distribution of Stroop costs")
axes[0].legend()

# Plot 2: each participant's change from congruent to incongruent
for subject in table.index:
    axes[1].plot([0, 1], [congruent[subject], incongruent[subject]],
                 color="gray", alpha=0.5, marker="o")
axes[1].plot([0, 1], [congruent.mean(), incongruent.mean()],
             color="red", linewidth=3, marker="o", label="Group mean")
axes[1].set_xticks([0, 1])
axes[1].set_xticklabels(["Congruent", "Incongruent"])
axes[1].set_ylabel("Mean reaction time (ms)")
axes[1].set_title("Condition difference per participant")
axes[1].legend()

plt.tight_layout()
plt.savefig("stroop_plots.png", dpi=150)
plt.show()

