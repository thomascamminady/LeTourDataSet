#!/usr/bin/env python3
"""
Reconstruct the general classification for the newest edition when the
source site does not yet publish a final GC table on the year page.

⚠️  This is a stopgap: the reconstruction sums per-stage times and
therefore ignores time bonuses and penalties, and it can only rank
riders who appear in every stage classification. Once the official GC
appears on letour.fr / letourfemmes.fr, a regular `make update`
replaces the reconstructed rows with official data (commit that
replacement with a '[data-fix]' marker).
"""

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent


def format_time(total_seconds: int) -> str:
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}h {minutes:02d}' {seconds:02d}''"


def format_gap(gap_seconds: int) -> str:
    if gap_seconds == 0:
        return "-"
    return f"+ {format_time(gap_seconds)}"


def lookup_total_distance(stages_file: Path, year: int) -> int:
    """Total distance of the edition from the stages file, 0 if unknown."""
    if not stages_file.exists():
        return 0
    stages = pd.read_csv(stages_file, low_memory=False)
    distances = stages.loc[stages["Year"] == year, "TotalTDFDistance"]
    if distances.empty:
        return 0
    return int(distances.iloc[0])


def fix_riders_history_file(data_dir: Path, competition: str) -> bool:
    """Reconstruct the newest edition's GC if it is missing. Returns True
    when the riders history file was updated."""
    riders_file = data_dir / f"{competition}_Riders_History.csv"
    all_rankings_file = data_dir / f"{competition}_All_Rankings_History.csv"
    stages_file = data_dir / f"{competition}_Stages_History.csv"

    if not riders_file.exists() or not all_rankings_file.exists():
        print(f"⚠️  Missing required files for {competition} in {data_dir}")
        return False

    riders_df = pd.read_csv(riders_file, low_memory=False)
    all_rankings_df = pd.read_csv(all_rankings_file, low_memory=False)

    latest_year_all = int(all_rankings_df["Year"].max())
    latest_year_riders = int(riders_df["Year"].max()) if not riders_df.empty else 0

    print(f"📊 {competition}: Latest year in all rankings: {latest_year_all}")
    print(f"📊 {competition}: Latest year in riders history: {latest_year_riders}")

    if latest_year_all <= latest_year_riders:
        print(f"✅ {competition}: Riders history is up to date")
        return False

    print(
        f"🔧 {competition}: Reconstructing the GC from stage data for "
        f"{latest_year_all}..."
    )
    print(
        f"⚠️  {competition}: Reconstructed times EXCLUDE time bonuses and "
        "penalties; replace them with official data once available."
    )

    latest_year_data = all_rankings_df[all_rankings_df["Year"] == latest_year_all]
    individual_data = latest_year_data[
        latest_year_data["Ranking type"] == "Individual (Stage)"
    ]

    if individual_data.empty:
        print(
            f"⚠️  {competition}: No individual stage data found for "
            f"{latest_year_all}"
        )
        return False

    # Only riders present in every stage classification can be ranked
    rider_stage_counts = individual_data["Rider"].value_counts()
    max_stages = int(rider_stage_counts.max())
    complete_riders = rider_stage_counts[rider_stage_counts == max_stages].index
    dropped = int((rider_stage_counts != max_stages).sum())
    print(
        f"📊 {competition}: {len(complete_riders)} riders completed all "
        f"{max_stages} stages"
    )
    if dropped:
        print(
            f"⚠️  {competition}: {dropped} rider(s) missing from at least one "
            "stage classification are NOT ranked"
        )

    complete_data = individual_data[individual_data["Rider"].isin(complete_riders)]
    gc_data = (
        complete_data.groupby("Rider")
        .agg(TotalSeconds=("TotalSeconds", "sum"), Team=("Team", "first"))
        .reset_index()
        .sort_values("TotalSeconds", kind="stable")
        .reset_index(drop=True)
    )
    gc_data["GapSeconds"] = gc_data["TotalSeconds"] - gc_data["TotalSeconds"].iloc[0]

    distance = lookup_total_distance(stages_file, latest_year_all)
    if distance == 0:
        print(
            f"⚠️  {competition}: Total distance for {latest_year_all} unknown; "
            "writing 0 — backfill it when the official number is published."
        )

    winner = gc_data.iloc[0]
    print(
        f"🏆 {competition}: Winner: {winner['Rider']} with "
        f"{winner['TotalSeconds'] / 3600:.1f}h total time (bonuses excluded)"
    )

    new_riders_df = pd.DataFrame(
        {
            "Rank": range(1, len(gc_data) + 1),
            "Rider": gc_data["Rider"],
            "Rider No.": pd.NA,
            "Team": gc_data["Team"],
            "Times": gc_data["TotalSeconds"].astype(int).map(format_time),
            "Gap": gc_data["GapSeconds"].astype(int).map(format_gap),
            "B": pd.NA,
            "P": pd.NA,
            "Year": latest_year_all,
            "Distance (km)": distance,
            "Number of stages": max_stages,
            "ResultType": "time",
            "TotalSeconds": gc_data["TotalSeconds"].astype(int),
            "GapSeconds": gc_data["GapSeconds"].astype(int),
        }
    )

    riders_df = riders_df[riders_df["Year"] != latest_year_all]
    updated = pd.concat([riders_df, new_riders_df], ignore_index=True)
    updated = updated.sort_values(["Year", "Rank"], kind="stable")
    updated.to_csv(riders_file, index=False)

    print(
        f"✅ {competition}: Added {len(new_riders_df)} riders with "
        "reconstructed GC times"
    )
    return True


def main() -> int:
    print("🔧 Starting riders history fix process...")

    base_dir = REPO_ROOT / "data"
    fixes_applied = False
    errors = False

    for subdir, competition, emoji in (
        ("men", "TDF", "🚹"),
        ("women", "TDFF", "🚺"),
    ):
        data_dir = base_dir / subdir
        if not data_dir.exists():
            print(f"⚠️  {competition} data directory not found: {data_dir}")
            continue
        print(f"\n{emoji} Processing {competition} data in {data_dir}")
        try:
            if fix_riders_history_file(data_dir, competition):
                fixes_applied = True
        except Exception as e:
            print(f"❌ Error processing {competition} data: {e}")
            errors = True

    if errors:
        print("\n❌ Riders history fix finished with errors")
        return 1
    if fixes_applied:
        print("\n✅ Riders history fix completed with updates")
    else:
        print("\n✅ Riders history fix completed - no updates needed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
