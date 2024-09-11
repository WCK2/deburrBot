import json
import os
import requests
import threading
import time
from PyQt5.QtCore import QThread, pyqtSignal
from utils.config import settings, idata
from utils.memory import mem


def post_req_async(path, data):
    """Send a POST request asynchronously."""
    url = settings.robot_url + path

    def send_post_request():
        try:
            response = requests.post(url, json=data, timeout=5)
            print(f'POST response: {response.status_code}, {response.text}')
        except requests.RequestException as e:
            print(f'Error sending POST request: {e}')

    # Create and start a new thread for the POST request
    threading.Thread(target=send_post_request, daemon=True).start()


def post_req_sync(path, data):
    url = settings.robot_url + path

    try:
        response = requests.post(url, json=data, timeout=5)
        
        # Print the status code and content-type for debugging
        print(f'Status Code: {response.status_code}')
        print(f'Content-Type: {response.headers.get("Content-Type")}')

        # Check the Content-Type of the response
        content_type = response.headers.get('Content-Type', '')

        if 'application/json' in content_type:
            try:
                # Convert the response text to a Python dictionary
                response_data = response.json()
                print("Parsed JSON data:", response_data)
                return response_data
            except ValueError as e:
                print("Error parsing JSON:", e)
                return None
        elif 'text/html' in content_type:
            # If the response is HTML, return the text content
            print("Received HTML response.")
            return response.text
        else:
            print("Received non-JSON, non-HTML response.")
            return response.text  # You might still want to return the raw text for other content types


    except requests.Timeout:
        print("The request timed out.")
        return None
    except requests.RequestException as e:
        print(f'Error sending POST request: {e}')
        return None


def get_req(path, data=None):
    """Send a GET request to the server to retrieve data based on the specified path and parameters."""
    url = settings.robot_url + path

    try:
        response = requests.get(url, params=data)

        # Check if the request was successful
        if response.status_code == 200:
            # Attempt to parse the JSON response
            response_data = response.json()
            print(f"Successfully retrieved data from {path}: {response_data}")
            return response_data
        elif response.status_code == 400:
            print(f"Bad request: {response.json().get('error')}")
        elif response.status_code == 404:
            print("Resource not found.")
        else:
            print(f"Error: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None




if __name__=="__main__":
    # response = post_req_sync(path='mem', data={'name': 'program', 'value': 999})
    # print(response, type(response))

    robot_pose = get_req(path='robot', params={'name': 'tcp_pose'})
    print(robot_pose)

    # response = post_req_sync(path='mem', data={'name': 'generator1_target_pairs', 'value': np.array([[0,1,2,3,4], [5,6,7,8,9,10]])})
    # print(response, type(response))
    


