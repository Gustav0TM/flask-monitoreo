import datetime

latest_agent_data = {}

def save_agent_data(data):
    hostname = data.get("hostname")
    if hostname:
        data["timestamp"] = int(datetime.datetime.now().timestamp())
        
        

        latest_agent_data[hostname] = data

def get_all_agent_data():
    return latest_agent_data

def format_datetime(timestamp):
    if timestamp is None:
        return "N/A"
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
