from gen import Calculate
import random
import json
import sys

verified_users = [
    'ItwG3moqIZamp7KxbEMcVmXVUcC2', 'ObMWsZhi8YMBFDjnjywgyZqdv4v1', 'UWe2lijRJdWSl3BDmXvUyLqShzH2', 'aEyNmr24vnSdNBDTZhCLVpqFwAv1', 'dq1abAfRnTTLVoTVxr1LK4gNfNb2', 'ejPSf2K5XDTCUwoJQosO1nHOfJ62'
]

def authUser(uid):
    if uid in verified_users:
        if random.random() < 0.05:
            from google.oauth2 import service_account
            from google.cloud import firestore

            creds = service_account.Credentials.from_service_account_file("service.json")
            db = firestore.Client(credentials=creds)

            request_count_ref = db.collection('requestCounts').document(uid)
            request_count_ref.set(
                {'count': firestore.Increment(1)}, 
                merge=True
            )

        return True
    
    try:
        from google.oauth2 import service_account
        from google.cloud import firestore

        creds = service_account.Credentials.from_service_account_file("service.json")
        db = firestore.Client(credentials=creds)

        user_doc_ref = db.collection('users').document(uid)
        user_doc = user_doc_ref.get()
        
        if not user_doc.exists:
            return False
        
        user_data = user_doc.to_dict()
        
        if not user_data.get('hasBotAccess', False):
            return False

        if random.random() < 0.1:
            request_count_ref = db.collection('requestCounts').document(uid)
            request_count_ref.set(
                {'count': firestore.Increment(1)}, 
                merge=True
            )
        
        return True
    
    except Exception as e:
        return False

def main():
    if len(sys.argv) != 10:
        result = {
            "success": False,
            "error": "Invalid number of arguments"
        }
        print(json.dumps(result))
        sys.exit(1)
    
    try:
        token_id = sys.argv[1]
        ua = sys.argv[2]
        path = sys.argv[3]
        endpoint = sys.argv[4]
        web_gl = sys.argv[5]
        region = sys.argv[6]
        endpointNoQuery = sys.argv[7] if sys.argv[7] else None
        fingerprint = sys.argv[8]
        uid = sys.argv[9]

        if not authUser(uid):
            result = {
                "success": False,
                "error": "Not authorized"
            }
            print(json.dumps(result))
            sys.exit(1)
        
        sign, key = Calculate(token_id, ua, path, endpoint, web_gl, region, endpointNoQuery, fingerprint)
        
        result = {
            "success": True,
            "sign": sign,
            "key": key
        }
        
        print(json.dumps(result))
        
    except Exception as e:
        result = {
            "success": False,
            "error": str(e)
        }
        print(json.dumps(result))
        sys.exit(1)

if __name__ == "__main__":
    main()
