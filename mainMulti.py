from flask import Flask, request, jsonify
from multiprocessing import Queue
import multiprocessing
from gen import *
import random
import os

app = Flask(__name__)

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

# Main

def calculate_worker(queue, token_id, ua, path, endpoint, web_gl, region, endpointNoQuery, fingerprint, uid):
    if not authUser(uid):
        queue.put({
            "success": False, 
            "error": "Not authorized"
        })

        return
    
    try:
        sign, key = Calculate(token_id, ua, path, endpoint, web_gl, region, endpointNoQuery, fingerprint)
        
        queue.put({
            "success": True, 
            "sign": sign, 
            "key": key
        })
    except Exception as e:
        queue.put({
            "success": False, 
            "error": str(e)
        })

@app.route('/recalculate', methods=['GET', 'POST'])
def recalculate():
    try:
        if request.method == 'GET':
            params = request.args
        else:
            params = request.json if request.is_json else request.form
        
        token_id = params.get('tokenId')
        ua = params.get('ua')
        path = params.get('path')
        endpoint = params.get('endpoint')
        web_gl = params.get('webGl')
        region = params.get('region')
        endpointNoQuery = params.get('endpointNoQuery')
        fingerprint = params.get('fingerprint')
        uid = params.get('uid')
        
        if not all([token_id, path, endpoint, ua, web_gl, uid, region, fingerprint]):
            return jsonify({"error": "Missing required parameters"}), 400
        
        # Create a queue for inter-process communication
        result_queue = Queue()
        
        # Create the process
        process = multiprocessing.Process(
            target=calculate_worker,
            args=(result_queue, token_id, ua, path, endpoint, web_gl, region, endpointNoQuery, fingerprint, uid)
        )
        
        # Start the process
        process.start()
        
        # Wait for the process to complete
        process.join(timeout=30)
        
        # Check if process is still alive
        if process.is_alive():
            print("Calculate process timed out, terminating...")
            process.terminate()
            process.join()
            return jsonify({"error": "Calculate function timed out"}), 500
        
        # Check if process exited with error
        if process.exitcode != 0:
            return jsonify({"error": f"Calculate process failed with exit code {process.exitcode}"}), 500
        
        # Get the result from the queue
        if not result_queue.empty():
            result = result_queue.get()
            
            if result["success"]:
                response_data = {
                    "sign": result["sign"],
                    "key": result["key"]
                }

                return jsonify(response_data), 200
            else:
                return jsonify({"error": result["error"]}), 500
        else:
            return jsonify({"error": "No result from Calculate function"}), 500
            
    except Exception as e:
        print("Exception caught in Recalculate: " + str(e))
        return jsonify({"error": str(e)}), 500

def solver_worker(queue, proxy, path, endpoint, ua, sec_ch_ua, chrome_full_version, region, ip, endpointNoQuery, uid):
    if not authUser(uid):
        queue.put({
            "success": False, 
            "error": "Not authorized"
        })

        return
    
    try:
        Did, Token, Fingerprint, Key, Sign, WebGl = Solver(
            proxy, 
            path, 
            endpoint, 
            ua, 
            sec_ch_ua, 
            chrome_full_version, 
            region,
            ip,
            endpointNoQuery
        ).makeSession(True)
        
        queue.put({
            "success": True,
            "did": Did,
            "token": Token,
            "fingerprint": Fingerprint,
            "key": Key,
            "sign": Sign,
            "webgl": WebGl
        })
    except Exception as e:
        queue.put({
            "success": False,
            "error": str(e)
        })

@app.route('/gen', methods=['GET', 'POST'])
def gen():
    try:
        if request.method == 'GET':
            params = request.args
        else:
            params = request.json if request.is_json else request.form
        
        proxy = params.get('proxy')
        path = params.get('path')
        endpoint = params.get('endpoint')
        ua = params.get('ua')
        sec_ch_ua = params.get('secChUa')
        chrome_full_version = params.get('chromeFullVersion')
        region = params.get('region')
        ip = params.get('ip')
        endpointNoQuery = params.get('endpointNoQuery')
        uid = params.get('uid')
        
        if not all([proxy, path, endpoint, ua, sec_ch_ua, chrome_full_version, uid, region]):
            return jsonify({"error": "Missing required parameters"}), 400
                
        # Create a queue for inter-process communication
        result_queue = Queue()
        
        # Create the process
        process = multiprocessing.Process(
            target=solver_worker,
            args=(result_queue, proxy, path, endpoint, ua, sec_ch_ua, chrome_full_version, region, ip, endpointNoQuery, uid)
        )
        
        # Start the process
        process.start()
        
        # Wait for the process to complete
        process.join(timeout=30)
        
        # Check if process is still alive
        if process.is_alive():
            print("Solver process timed out, terminating...")
            process.terminate()
            process.join()
            return jsonify({"error": "Solver function timed out"}), 500
        
        # Check if process exited with error
        if process.exitcode != 0:
            return jsonify({"error": f"Solver process failed with exit code {process.exitcode}"}), 500
        
        if not result_queue.empty():
            result = result_queue.get()
            
            if result["success"]:
                # Did seems to be depreciated, dont enforce
                if not all([result["token"], result["fingerprint"], result["key"], result["sign"], result["webgl"]]):
                    return jsonify({"error": "An error occured"}), 400

                response_data = {
                    "sign": result["sign"],
                    "key": result["key"],
                    "token": result["token"],
                    "webGl": result["webgl"],
                    "did": result["did"],
                    "fp": result["fingerprint"]
                }
                
                return jsonify(response_data), 200
            else:
                return jsonify({"error": result["error"]}), 500
        else:
            return jsonify({"error": "No result from Solver function"}), 500
            
    except Exception as e:
        print("Exception caught in Gen: " + str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
