from flask import Flask, jsonify, request
import json, os
from datetime import datetime
from flask import Flask, request
from flask_cors import CORS  # <-- Import CORS


app = Flask(__name__)
CORS(app,origins=["chrome-extension://bachipeoekbkldoaffnaaidkbnimoijm"])  # <-- Enable CORS for all routes

print("Starting server...")
LOG = "log.json"

def load():
    now = datetime.now()
    if not os.path.exists(LOG):
        return {"date": str(datetime.now().date()), "productive": 0, "unproductive": 0, "domains": {},"productivity":0}
    with open(LOG) as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            # If file is empty or invalid JSON, reset it
            return {"date": str(datetime.now().date()), "productive": 0, "unproductive": 0, "domains": {},"productivity":0}
    if data["date"] != str(datetime.now().date()):
        return {"date": str(datetime.now().date()), "productive": 0, "unproductive": 0, "domains": {},"productivity":0}
    return data

def save(data):
    now =datetime.now()

    if (now.hour * 3600 + now.minute * 60 + now.second) == 0:
        data["productivity"] = 0
    elif data["productive"] < 7200:
        data["productivity"] = 0
    elif (now.hour * 3600 + now.minute * 60 + now.second) < 43200:
        data["productivity"] = ((int(data["productive"]-data["unproductive"])+18000)/43200)*100
    elif (now.hour * 3600 + now.minute * 60 + now.second) < 57600:
        data["productivity"] = ((int(data["productive"]-data["unproductive"])+18000)/57600)*100
    else:    
        data["productivity"]= int(((data["productive"]-data["unproductive"]))/(now.hour * 3600 + now.minute * 60 + now.second))*100 
    with open(LOG, "w") as f:
        json.dump(data, f, indent=2)
@app.route("/log_time", methods=["POST"])
def log_time():
    data = load()
    incoming = request.json  # expects { "domain": "...", "seconds": 60, "timestamp": "..." }

    if not incoming or "domain" not in incoming or "seconds" not in incoming:
        return {"status": "error", "message": "Invalid data"}, 400

    domain = incoming["domain"]
    seconds = incoming["seconds"]
    timestamp = incoming.get("timestamp")  # Optional, for logging or future use

    if "history" not in data:
            data["history"] = {} 

    # Store time per domain
    data["domains"][domain] = data["domains"].get(domain, 0) + seconds

    # Productivity logic
    if domain in ["pw.live","www.pw.live"]:
        data["productive"] += seconds
       
          # Append to history only for productive domain
        data["history"].setdefault(domain, []).append({
            "timestamp": timestamp,
            "seconds": seconds 
        })
    elif domain in ["www.youtube.com", "www.twitch.tv", "www.reddit.com", "www.twitter.com"]:
        data["unproductive"] += seconds * 2
    else:
        data["unproductive"] += seconds
    # Store last timestamp per domain
    if "last_timestamp" not in data:
        data["last_timestamp"] = {}
    data["last_timestamp"][domain] = timestamp    

    # Optionally, store or log the timestamp if you want
    # Example: data.setdefault("timestamps", []).append({"domain": domain, "timestamp": timestamp, "seconds": seconds})

    save(data)
    return {"status": "ok"}
@app.route("/get_block_status")
def get_block_status():
    now = datetime.now()
    data = load()
    productiy = data["productivity"]

    # Unlock rewards based on time
    rulestokill = []
    if now.hour < 12:
        if productiy >= 60 :  
            rulestokill.append(5)
            if productiy >= 66:  # 1 hour
                 rulestokill.append(3)
            if productiy >= 75:  # 2 hours
                rulestokill.append(4)
            if productiy >= 90:
                rulestokill.append(2)
    elif now.hour < 16:
        if productiy >= 63 :  
            rulestokill.append(5)
            if productiy >= 66:  # 1 hour
                 rulestokill.append(3)
            if productiy >= 75:  # 2 hours
                rulestokill.append(4)
            if productiy >= 90:
                rulestokill.append(2)
    else:
        if productiy >= 45 :  
            rulestokill.append(5)
            if productiy >= 50:  # 1 hour
                 rulestokill.append(3)
            if productiy >= 55 :  # 2 hours
                rulestokill.append(4)
            if productiy >= 65:
                rulestokill.append(2)           


    return {"unblock_rule_ids": rulestokill}


if __name__ == "__main__":
    print("app will start")
    try:
        app.run(port=5000)
    except Exception as e:
        print("Error starting server:", e)    
