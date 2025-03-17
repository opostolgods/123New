import requests

def get_ip_info(ip):
    """
    Get information about an IP address using ip-api.com
    
    Args:
        ip (str): The IP address to look up
        
    Returns:
        dict: Information about the IP address
    """
    url = f"http://ip-api.com/json/{ip}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "fail", "message": f"API returned status code {response.status_code}"}
    except Exception as e:
        return {"status": "fail", "message": str(e)}

