#!/usr/bin/env python3
"""
Fix riders history files by extracting general classification from all rankings data.
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

def fix_riders_history_file(data_dir: Path, competition: str) -> bool:
    riders_file = data_dir / f"{competition}_Riders_History.csv"
    all_rankings_file = data_dir / f"{competition}_All_Rankings_History.csv"
    
    if not riders_file.exists() or not all_rankings_file.exists():
        print(f"⚠️  Missing required files for {competition} in {data_dir}")
        return False
    
    try:
        riders_df = pd.read_csv(riders_file)
        all_rankings_df = pd.read_csv(all_rankings_file, low_memory=False)
        
        latest_year_all = all_rankings_df['Year'].max()
        latest_year_riders = riders_df['Year'].max() if not riders_df.empty else 0
        
        print(f"📊 {competition}: Latest year in all rankings: {latest_year_all}")
        print(f"📊 {competition}: Latest year in riders history: {latest_year_riders}")
        
        if latest_year_all <= latest_year_riders:
            print(f"✅ {competition}: Riders history is up to date")
            return False
        
        print(f"🔧 {competition}: Calculating GC from stage data for {latest_year_all}...")
        
        latest_year_data = all_rankings_df[all_rankings_df['Year'] == latest_year_all]
        individual_data = latest_year_data[latest_year_data['Ranking type'] == 'Individual (Stage)']
        
        if individual_data.empty:
            print(f"⚠️  {competition}: No individual stage data found for {latest_year_all}")
            return False
        
        print(f"📈 {competition}: Found {len(individual_data)} individual stage results")
        
        # Calculate general classification by summing stage times
        # Only include riders who completed ALL stages - determine max stages dynamically
        rider_stage_counts = individual_data['Rider'].value_counts()
        max_stages = rider_stage_counts.max()
        complete_riders = rider_stage_counts[rider_stage_counts == max_stages].index.tolist()
        
        print(f"📊 {competition}: {len(complete_riders)} riders completed all {max_stages} stages")
        
        complete_data = individual_data[individual_data['Rider'].isin(complete_riders)]
        
        gc_data = (
            complete_data.groupby('Rider')
            .agg({
                'TotalSeconds': 'sum',
                'Team': 'first',
            })
            .reset_index()
        )
        
        gc_data = gc_data.sort_values('TotalSeconds')
        winner_time = gc_data.iloc[0]['TotalSeconds']
        gc_data['GapSeconds'] = gc_data['TotalSeconds'] - winner_time
        
        print(f"🏆 {competition}: Winner: {gc_data.iloc[0]['Rider']} with {gc_data.iloc[0]['TotalSeconds']/3600:.1f}h total time")
        
        # Remove existing data for this year
        riders_df = riders_df[riders_df['Year'] != latest_year_all]
        
        # Create new riders data
        new_riders_data = []
        for i, (_, row) in enumerate(gc_data.iterrows(), 1):
            total_seconds = int(row['TotalSeconds'])
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if i == 1:
                gap_str = "-"
            else:
                gap_seconds = int(row['GapSeconds'])
                gap_hours = gap_seconds // 3600
                gap_minutes = (gap_seconds % 3600) // 60
                gap_secs = gap_seconds % 60
                gap_str = f"+ {gap_hours:02d}h {gap_minutes:02d}' {gap_secs:02d}''"
                
            time_str = f"{hours:02d}h {minutes:02d}' {seconds:02d}''"

            new_rider = {
                'Rank': i,
                'Rider': row['Rider'],
                'Rider No.': '',
                'Team': row['Team'],
                'Times': time_str,
                'Gap': gap_str,
                'B': '',
                'P': '',
                'Year': int(latest_year_all),
                'Distance (km)': 0,
                'Number of stages': max_stages,
                'ResultType': 'time',
                'TotalSeconds': int(row['TotalSeconds']),
                'GapSeconds': int(row['GapSeconds']),
            }
            new_riders_data.append(new_rider)
        
        new_riders_df = pd.DataFrame(new_riders_data)
        updated_riders_df = pd.concat([riders_df, new_riders_df], ignore_index=True)
        updated_riders_df = updated_riders_df.sort_values(['Year', 'Rank'])
        updated_riders_df.to_csv(riders_file, index=False)
        
        print(f"✅ {competition}: Added {len(new_riders_data)} riders with correct GC times")
        return True
        
    except Exception as e:
        print(f"❌ {competition}: Error: {e}")
        return False

def main():
    print("🔧 Starting riders history fix process...")
    
    base_dir = Path(__file__).parent.parent / "data"
    men_dir = base_dir / "men"
    women_dir = base_dir / "women"
    
    fixes_applied = False
    
    # Fix men's data
    if men_dir.exists():
        print(f"\n🚹 Processing men's data in {men_dir}")
        try:
            if fix_riders_history_file(men_dir, "TDF"):
                fixes_applied = True
        except Exception as e:
            print(f"❌ Error processing men's data: {e}")
    else:
        print(f"⚠️  Men's data directory not found: {men_dir}")
    
    # Fix women's data
    if women_dir.exists():
        print(f"\n🚺 Processing women's data in {women_dir}")
        try:
            if fix_riders_history_file(women_dir, "TDFF"):
                fixes_applied = True
        except Exception as e:
            print(f"❌ Error processing women's data: {e}")
    else:
        print(f"⚠️  Women's data directory not found: {women_dir}")
    
    if fixes_applied:
        print("\n✅ Riders history fix completed with updates")
    else:
        print("\n✅ Riders history fix completed - no updates needed")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
