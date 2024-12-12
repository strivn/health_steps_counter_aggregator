# %%
import pandas as pd
import json
import os
import logging

from datetime import datetime
from pathlib import Path
from syftbox.lib import Client
from typing import Tuple

# %%


# %%
# Defining logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# %%
def network_participants(datasite_path: Path):
    """Retrieves a list of user directories (participants) in a given datasite path."""
    entries = os.listdir(datasite_path)
    users = []
    
    for entry in entries:
        if Path(datasite_path / entry).is_dir():
            users.append(entry)
    
    return users

# %%
def get_network_steps_mean(
    datasites_path: Path, 
    peers: list[str]
):
    
    """Calculates the mean daily steps across network peers."""
    aggregated_step_count = {}
    aggregated_step_entries = {}
    aggregated_peers = {}

    for peer in peers:
        tracker_file = (
            datasites_path / peer / "api_data" / "health_steps_counter" / "health_steps_counter.json"
        )
        
        if not tracker_file.exists():
            continue

        try:
            with open(str(tracker_file), "r") as json_file:
                peer_data = json.load(json_file)
            
            for key, value in peer_data.items():
                if key in aggregated_step_count:
                    aggregated_step_count[key] += value['dp_step_count']
                else: 
                    aggregated_step_count[key] = value['dp_step_count']
                    
                
                if key in aggregated_step_entries:
                    aggregated_step_entries[key] += value['dp_step_entries']
                else: 
                    aggregated_step_entries[key] = value['dp_step_entries']
                    
                
                if key in aggregated_peers:
                    aggregated_peers[key] += 1
                else: 
                    aggregated_peers[key] = 1
                    
                    
        except json.JSONDecodeError:
            logging.warning(f"Could not decode JSON for peer {peer}")
            continue
        
        for key, value in aggregated_step_count.items():
            aggregated_step_count[key] /= aggregated_peers[key]

    return aggregated_step_count, aggregated_peers

# Modified generate_html_report function with participant count condition
# Modified generate_html_report function with reverse sort and sticky header
def generate_html_report(step_data: dict, peer_counts: dict, output_path: Path):
    """Generates an HTML report for the step data and participant counts."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Daily Steps Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                line-height: 1.6;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
            }}
            .stats-box {{
                background-color: #f5f5f5;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .table-container {{
                max-height: 600px;
                overflow-y: auto;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            thead {{
                position: sticky;
                top: 0;
                z-index: 1;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #4CAF50;
                color: white;
            }}
            tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
            .insufficient-data {{
                color: #999;
                font-style: italic;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Daily Steps Report</h1>
            <div class="stats-box">
                <h2>Overview</h2>
                <p>Total number of unique dates: {total_dates}</p>
                <p>Average number of participants per day: {avg_participants:.1f}</p>
            </div>
            
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Average Steps</th>
                            <th>Number of Participants</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Generate table rows with reverse sort
    table_rows = ""
    for date in sorted(step_data.keys(), reverse=True):
        formatted_date = datetime.fromisoformat(date).strftime('%Y-%m-%d')
        
        # Check if there's only 1 participant
        if peer_counts[date] <= 1:
            steps_display = '<span class="insufficient-data">Not enough participants</span>'
        else:
            steps_display = f"{step_data[date]:,.0f}"
            
        table_rows += f"""
                <tr>
                    <td>{formatted_date}</td>
                    <td>{steps_display}</td>
                    <td>{peer_counts[date]}</td>
                </tr>"""
    
    # Calculate summary statistics
    valid_dates = [date for date in step_data.keys() if peer_counts[date] > 1]
    total_dates = len(valid_dates)
    valid_participant_counts = [peer_counts[date] for date in valid_dates]
    avg_participants = sum(valid_participant_counts) / len(valid_participant_counts) if valid_participant_counts else 0
    
    # Fill in the template
    html_content = html_content.format(
        total_dates=total_dates,
        avg_participants=avg_participants,
        table_rows=table_rows
    )
    
    # Write the HTML file
    with open(output_path, 'w') as f:
        f.write(html_content)

# %%
if __name__ == '__main__':
    client = Client.load()

    peers = network_participants(client.datasite_path.parent)

    aggregated_step_count, peer_counts = get_network_steps_mean(client.datasite_path.parent, peers)

    output_public_file = client.datasite_path / "public" / "aggregated_daily_steps.json"
    
    with open(output_public_file, 'w') as f:
        json.dump(aggregated_step_count, f)
        
    output_html_file = client.datasite_path / "public" / "daily_steps_report.html"
    generate_html_report(aggregated_step_count, peer_counts, output_html_file)

# %%



