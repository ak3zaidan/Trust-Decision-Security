from google.oauth2 import service_account
from google.cloud import firestore
from datetime import datetime
import json

def serialize_firestore_data(data):
    """Convert Firestore types (e.g., datetime) to JSON-serializable format."""
    if isinstance(data, dict):
        return {k: serialize_firestore_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize_firestore_data(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data

def get_top_users_by_request_count(limit=3):
    # Authenticate
    creds = service_account.Credentials.from_service_account_file("TrustGen2/service.json")
    db = firestore.Client(credentials=creds)

    # Step 1: Query top N users by requestCount
    request_counts_ref = db.collection('requestCounts')
    top_users_query = request_counts_ref.order_by('count', direction=firestore.Query.DESCENDING).limit(limit)
    top_users = list(top_users_query.stream())

    # Step 2: For each user ID, get the user document and print with request count
    print(f"Top {limit} Users by Request Count:\n")
    for doc in top_users:
        uid = doc.id
        count = doc.to_dict().get('count', 0)
        user_doc = db.collection('users').document(uid).get()

        print(f"User ID: {uid}")
        print(f"Request Count: {count}")

        if user_doc.exists:
            user_data = serialize_firestore_data(user_doc.to_dict())
            print("User Document:")
            print(json.dumps(user_data, indent=4))
        else:
            print("User document not found.")
        
        print("\n" + "-"*40 + "\n")

get_top_users_by_request_count()
