import openneuro as on

on.download(
    dataset="ds000164",
    target_dir="ds000164",
    include=["*events.tsv"],
)