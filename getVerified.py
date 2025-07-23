from google.oauth2 import service_account
from google.cloud import firestore

def get_ids():
    # Authenticate with your service account
    creds = service_account.Credentials.from_service_account_file("TrustGen2/service.json")
    db = firestore.Client(credentials=creds)

    # Query for users with bot access
    users_ref = db.collection('users')
    query = users_ref.where('hasBotAccess', '==', True)
    results = query.stream()

    # Collect user IDs
    user_ids = [doc.id for doc in results]

    # Print as a Python array string
    print(user_ids)

get_ids()
