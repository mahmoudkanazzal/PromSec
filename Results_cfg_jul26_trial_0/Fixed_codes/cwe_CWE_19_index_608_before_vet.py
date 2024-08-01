import os
import requests

API_KEY = os.getenv('API_KEY')

def create_device(device_name):
    url = 'https://api.example.com/devices'
    headers = {'Authorization': 'Bearer ' + API_KEY}
    data = {'device_name': device_name}
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def delete_device(device_id):
    url = f'https://api.example.com/devices/{device_id}'
    headers = {'Authorization': 'Bearer ' + API_KEY}
    response = requests.delete(url, headers=headers)
    return response.json()

def list_devices():
    url = 'https://api.example.com/devices'
    headers = {'Authorization': 'Bearer ' + API_KEY}
    response = requests.get(url, headers=headers)
    return response.json()

def update_device(device_id, new_name):
    url = f'https://api.example.com/devices/{device_id}'
    headers = {'Authorization': 'Bearer ' + API_KEY}
    data = {'device_name': new_name}
    response = requests.put(url, headers=headers, json=data)
    return response.json()

def install_agent(device_id, agent_version):
    url = f'https://api.example.com/devices/{device_id}/install_agent'
    headers = {'Authorization': 'Bearer ' + API_KEY}
    data = {'agent_version': agent_version}
    response = requests.post(url, headers=headers, json=data)
    return response.json()