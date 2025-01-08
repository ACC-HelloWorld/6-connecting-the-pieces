import os
import json
import pandas as pd
from pymongo.mongo_client import MongoClient
from communication import to_sorted_rounded_frozenset_list

def test_orchestrator_client():
    """Test that the orchestrator client works correctly."""
    
    # Load test data files
    with open("session_id.txt") as f:
        session_id = f.read().strip()
        
    with open("payload_dicts.json") as f:
        orchestrator_payloads = json.load(f)
        
    with open("results.json") as f:
        results_dicts = json.load(f)

    # Extract RGB values from payloads
    orchestrator_rgb_values = [
        {k: v for k, v in payload["command"].items() if k in ("R", "G", "B")}
        for payload in orchestrator_payloads
    ]

    # Connect to MongoDB and verify data
    connection_string = os.environ["CONNECTION_STRING"]
    database_name = os.environ["DATABASE_NAME"] 
    collection_name = os.environ["COLLECTION_NAME"]

    client = MongoClient(connection_string)
    db = client[database_name]
    collection = db[collection_name]

    # Query documents with matching session_id
    mongo_results = list(collection.find({"session_id": session_id}))
    
    assert len(mongo_results) > 0, f"No MongoDB results found for session ID: {session_id}"

    # Create DataFrames and compare
    df_mongo = pd.json_normalize(mongo_results)
    df_results = pd.json_normalize(results_dicts)

    # Compare key fields
    fields_to_compare = ["command.R", "command.G", "command.B", 
                        "experiment_id", "session_id"]
    
    for field in fields_to_compare:
        assert df_mongo[field].tolist() == df_results[field].tolist(), \
            f"Mismatch in {field} between MongoDB and results.json"

    # Verify optimization results are saved
    assert os.path.exists("optimization_trace.png"), "Optimization trace plot not saved"
    assert os.path.exists("results.csv"), "Results CSV not saved"

    client.close()
