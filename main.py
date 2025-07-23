from flask import Flask, request, jsonify
import subprocess
import json
import os

app = Flask(__name__)

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
                
        # Prepare arguments for subprocess
        args = [
            'python', 'calculate_worker.py',
            token_id, ua, path, endpoint, web_gl, region, 
            endpointNoQuery if endpointNoQuery else '', fingerprint, uid
        ]
        
        try:
            # Run subprocess with timeout
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else f"Process failed with exit code {result.returncode}"
                return jsonify({"error": error_msg}), 500
            
            # Parse the JSON output
            output_data = json.loads(result.stdout.strip())
            
            if output_data["success"]:
                response_data = {
                    "sign": output_data["sign"],
                    "key": output_data["key"]
                }
                return jsonify(response_data), 200
            else:
                return jsonify({"error": output_data["error"]}), 500
                
        except subprocess.TimeoutExpired:
            return jsonify({"error": "Calculate function timed out"}), 500
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid response from calculate worker"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500
            
    except Exception as e:
        print("Exception caught in Recalculate: " + str(e))
        return jsonify({"error": str(e)}), 500

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
        
        if not all([path, endpoint, ua, sec_ch_ua, chrome_full_version, uid, region]):
            return jsonify({"error": "Missing required parameters"}), 400
        
        # Prepare arguments for subprocess
        args = [
            'python', 'solver_worker.py',
            proxy, path, endpoint, ua, sec_ch_ua, chrome_full_version, 
            region, ip if ip else '', endpointNoQuery if endpointNoQuery else '', uid
        ]
        
        try:
            # Run subprocess with timeout
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else f"Process failed with exit code {result.returncode}"

                return jsonify({"error": error_msg}), 500
            
            # Parse the JSON output
            output_data = json.loads(result.stdout.strip())
            
            if output_data["success"]:
                # Did seems to be depreciated, dont enforce
                if not all([output_data["token"], output_data["fingerprint"], output_data["key"], output_data["sign"], output_data["webgl"]]):
                    return jsonify({"error": "An error occured"}), 400

                response_data = {
                    "sign": output_data["sign"],
                    "key": output_data["key"],
                    "token": output_data["token"],
                    "webGl": output_data["webgl"],
                    "did": output_data["did"],
                    "fp": output_data["fingerprint"]
                }
                
                return jsonify(response_data), 200
            else:
                return jsonify({"error": output_data["error"]}), 500
                
        except subprocess.TimeoutExpired:
            return jsonify({"error": "Solver function timed out"}), 500
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid response from solver worker"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500
            
    except Exception as e:        
        print("Exception caught in Gen: " + str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
