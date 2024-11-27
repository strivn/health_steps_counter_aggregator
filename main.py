# %%
import pandas as pd
import json
import os
import logging

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
) -> Tuple[float, list[str]]:
    
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
            continue
        
        for key, value in aggregated_step_count.items():
            aggregated_step_count[key] /= aggregated_peers[key]

    return aggregated_step_count

# %%
if __name__ == '__main__':
    client = Client.load()

    peers = network_participants(client.datasite_path.parent)

    aggregated_step_count = get_network_steps_mean(client.datasite_path.parent, peers)

    output_public_file = client.datasite_path / "public" / "aggregated_daily_steps.json"
    
    with open(output_public_file, 'w') as f:
        json.dump(aggregated_step_count, f)
# %%



