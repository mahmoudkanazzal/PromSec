import os
import requests

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
BASE_URL = 'https://api.example.com/devices'

def create_device(device_data):
    headers = {'Authorization': f'Bearer {API_KEY}:{API_SECRET}'}
    response = requests.post(BASE_URL, headers=headers, json=device_data)
    return response.json()

def delete_device(device_id):
    headers = {'Authorization': f'Bearer {API_KEY}:{API_SECRET}'}
    response = requests.delete(f'{BASE_URL}/{device_id}', headers=headers)
    return response.json()

def list_devices():
    headers = {'Authorization': f'Bearer {API_KEY}:{API_SECRET}'}
    response = requests.get(BASE_URL, headers=headers)
    return response.json()

def update_device(device_id, updated_data):
    headers = {'Authorization': f'Bearer {API_KEY}:{API_SECRET}'}
    response = requests.put(f'{BASE_URL}/{device_id}', headers=headers, json=updated_data)
    return response.json()

def install_agent(device_id, agent_data):
    headers = {'Authorization': f'Bearer {API_KEY}:{API_SECRET}'}
    response = requests.post(f'{BASE_URL}/{device_id}/install', headers=headers, json=agent_data)
    return response.json()