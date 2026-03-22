import requests
import time

def benchmark_api():
    base_url = 'http://127.0.0.1:5000'
    
    # 1. Authenticate to get the JWT session token
    # Using the placeholder regular user we set up earlier
    login_payload = {
        'username': 'user_ananya', 
        'password': 'password1'
    }
    
    print("Logging in to get session token...")
    try:
        login_res = requests.post(f"{base_url}/login", json=login_payload)
        login_res.raise_for_status()
        token = login_res.json().get('session_token')
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect. Is your Flask app running? Error: {e}")
        return

    headers = {'Authorization': f'Bearer {token}'}
    
    # 2. Hit the endpoint 50 times to get a stable average
    print("Benchmarking GET /api/bookings...")
    
    start_time = time.time()
    for _ in range(50):
        res = requests.get(f"{base_url}/api/bookings", headers=headers)
        # Check if the request was actually successful (status 200)
        if res.status_code != 200:
            print(f"API returned an error: {res.status_code}")
            return
            
    end_time = time.time()
    
    # Calculate average time in milliseconds
    avg_api_time = ((end_time - start_time) / 50) * 1000
    print(f"Average API Response Time: {avg_api_time:.2f} ms")

if __name__ == '__main__':
    benchmark_api()