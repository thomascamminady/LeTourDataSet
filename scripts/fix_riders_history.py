#!/usr/bin/env python3
"""
Fix riders history files by extracting general classification from all rankings data.

This script checks if the latest year's data is missing from riders history files
and extracts it from the all rankings data if needed. It's designed to be robust
for future years and different data structures.
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

def fix_riders_history_file(data_dir: Path, competition: str) -> bool:
    """
    Fix riders history file for a given competition.
    
    Args:
        data_dir: Path to the data directory (men/ or women/)
        competition: Competition prefix (TDF or TDFF)
    
    Returns:
        bool: True if fixes were applied, False if no fixes needed
    """
    riders_file = data_dir / f"{competition}_Riders_History.csv"
    all_rankings_file = data_dir / f"{competition}_All_Rankings_History.csv"
    
    if not riders_file.exists() or not all_rankings_file.exists():
        print(f"⚠️  Missing required files for {competition} in {data_dir}")
        return False
    
    try:
        # Read the data
        riders_df = pd.read_csv(riders_file)
        all_rankings_df = pd.read_csv(all_rankings_file)
        
        # Get the latest year in all rankings
        latest_year_all = all_rankings_df['Year'].max()
        
        # Get the latest year in riders history
        latest_year_riders = riders_df['Year'].max() if not riders_df.empty else 0
        
        print(f"📊 {competition}: Latest year in all rankings: {latest_year_all}")
        print(f"📊 {competition}: Latest year in riders history: {latest_year_riders}")
        
        if latest_year_all <= latest_year_riders:
            print(f"✅ {competition}: Riders history is up to date")
            return False
        
        print(f"🔧 {competition}: Extracting {latest_year_all} data from all rankings...")
        
        # Extract the latest year's final classification
        latest_year_data = all_rankings_df[all_rankings_df['Year'] == latest_year_all]
        
        if latest_year_data.empty:
            print(f"⚠️  {competition}: No data found for {latest_year_all}")
            return False
        
        # Find the final stage (highest stage number)
        final_stage = latest_year_data['Stage'].max()
        final_stage_data = latest_year_data[latest_year_data['Stage'] == final_stage]
        
        if final_stage_data.empty:
            print(f"⚠️  {competition}: No final stage data found for {latest_year_all}")
            return False
        
        print(f"📈 {competition}: Extracting from stage {final_stage} of {latest_year_all}")
        
        # Create riders history format
        # Sort by TotalSeconds (ascending) to get proper ranking
        final_stage_data = final_stage_data.sort_values('TotalSeconds')
        
        # Remove duplicates (keep first occurrence of each rider)
        final_stage_data = final_stage_data.drop_duplicates(subset=['RiderName'], keep='first')
        
        # Create new riders data in the correct format
        new_riders_data = []
        for i, (_, row) in enumerate(final_stage_data.iterrows(), 1):
            new_rider = {
                'Year': int(latest_year_all),
                'Rank': i,
                'RiderName': row['RiderName'],
                'Team': row.get('Team', ''),
                'TotalSeconds': row['TotalSeconds']
            }
            new_riders_data.append(new_rider)
        
        # Convert to DataFrame
        new_riders_df = pd.DataFrame(new_riders_data)
        
        # Append to existing riders data
        updated_riders_df = pd.concat([riders_df, new_riders_df], ignore_index=True)
        
        # Sort by Year and then by Rank
        updated_riders_df = updated_riders_df.sort_values(['Year', 'Rank'])
        
        # Save the updated file
        updated_riders_df.to_csv(riders_file, index=False)
        
        print(f"✅ {competition}: Added {len(new_riders_data)} riders from {latest_year_all}")
        print(f"💾 {competition}: Updated {riders_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ {competition}: Error processing data: {e}")
        return False

def main():
    """Main function to fix both men's and women's riders history."""
    print("🔧 Starting riders history fix process...")
    print(f"📅 Current year: {datetime.now().year}")
    
    # Define data directories
    base_dir = Path(__file__).parent.parent / "data"
    men_dir = base_dir / "men"
    women_dir = base_dir / "women"
    
    fixes_applied = False
    
    # Fix men's data
    if men_dir.exists():
        print(f"\n🚹 Processing men's data in {men_dir}")
        if fix_riders_history_file(men_dir, "TDF"):
            fixes_applied = True
    else:
        print(f"⚠️  Men's data directory not found: {men_dir}")
    
    # Fix women's data
    if women_dir.exists():
        print(f"\n🚺 Processing women's data in {women_dir}")
        if fix_riders_history_file(women_dir, "TDFF"):
            fixes_applied = True
    else:
        print(f"⚠️  Women's data directory not found: {women_dir}")
    
    if fixes_applied:
        print("\n✅ Riders history fix completed with updates")
        return 0
    else:
        print("\n✅ Riders history fix completed - no updates needed")
        return 0

if __name__ == "__main__":
    sys.exit(main())
