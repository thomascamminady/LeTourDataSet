#!/usr/bin/env python3
"""
Fix the 2025 riders history by extracting general classification from all rankings data.
"""

import pandas as pd

def main():
    # Read the current riders history and all rankings
    riders_history = pd.read_csv('data/women/TDFF_Riders_History.csv')
    all_rankings = pd.read_csv('data/women/TDFF_All_Rankings_History.csv')
    
    print(f"Current riders history has {len(riders_history)} entries")
    print(f"Years in riders history: {sorted(riders_history['Year'].unique())}")
    
    # Extract 2025 general classification from all rankings
    # We need to find the final overall general classification, not stage results
    # Look for entries that appear to be the final GC (lowest GapSeconds with meaningful times)
    df_2025 = all_rankings[
        (all_rankings['Year'] == 2025) & 
        (all_rankings['ResultType'] == 'time') &
        (all_rankings['Times'].notna()) &
        (all_rankings['Stages'] == 9)  # Final stage
    ].copy()
    
    if len(df_2025) == 0:
        print("No 2025 final stage data found!")
        return
    
    # Sort by TotalSeconds to get proper general classification ranking
    df_2025 = df_2025.sort_values('TotalSeconds')
    
    # Remove duplicates by keeping the entry with lowest TotalSeconds for each rider
    df_2025 = df_2025.drop_duplicates(subset=['Rider'], keep='first')
    
    # Filter out entries without proper times (some might be intermediate results)
    df_2025 = df_2025[df_2025['TotalSeconds'] > 0]
    
    # Reset rank to be sequential 1, 2, 3, etc.
    df_2025 = df_2025.reset_index(drop=True)
    df_2025['Rank'] = df_2025.index + 1
    
    # Add missing 'Rider No.' column with NaN values (since it's not in all rankings data)
    df_2025['Rider No.'] = None
    
    # Select and reorder columns to match riders history format
    columns_order = ['Rank', 'Rider', 'Rider No.', 'Team', 'Times', 'Gap', 'B', 'P', 
                     'Year', 'Distance (km)', 'Number of stages', 'ResultType', 
                     'TotalSeconds', 'GapSeconds']
    
    df_2025_gc = df_2025[columns_order].copy()
    
    # Update ResultType to match historical format
    df_2025_gc['ResultType'] = 'time'
    
    print(f"Found {len(df_2025_gc)} riders in 2025 general classification")
    print(f"Winner: {df_2025_gc.iloc[0]['Rider']} ({df_2025_gc.iloc[0]['Team']})")
    print(f"Time: {df_2025_gc.iloc[0]['Times']}")
    
    # Append 2025 data to riders history
    updated_riders_history = pd.concat([riders_history, df_2025_gc], ignore_index=True)
    
    # Save updated file
    updated_riders_history.to_csv('data/women/TDFF_Riders_History.csv', index=False)
    
    print(f"Updated riders history now has {len(updated_riders_history)} entries")
    print(f"Years now include: {sorted(updated_riders_history['Year'].unique())}")
    
    # Show top 10 from 2025
    print("\nTop 10 from 2025 Tour de France Femmes:")
    for i in range(min(10, len(df_2025_gc))):
        rider = df_2025_gc.iloc[i]
        print(f"{rider['Rank']}. {rider['Rider']} ({rider['Team']}) - {rider['Times']} {rider['Gap']}")

if __name__ == "__main__":
    main()
