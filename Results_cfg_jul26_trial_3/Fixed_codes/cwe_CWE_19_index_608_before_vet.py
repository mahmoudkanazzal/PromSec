import os
import requests

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
BASE_URL = 'https://api.example.com'

def create_device(device_data):
    url = f'{BASE_URL}/devices'
    headers = {'Authorization': f'Bearer {API_KEY}:{API_SECRET}'}
    response = requests.post(url, json=device_data, headers=headers)
    return response.json()

def delete_device(device_id):
    url = f'{BASE_URL}/devices/{device_id}'
    headers = {'Authorization': f'Bearer {API_KEY}:{API_SECRET}'}
    response = requests.delete(url, headers=headers)
    return response.json()

def list_devices():
    url = f'{BASE_URL}/devices'
    headers = {'Authorization': f'Bearer {API_KEY}:{API_SECRET}'}
    response = requests.get(url, headers=headers)
    return response.json()

def update_device(device_id, updated_data):
    url = f'{BASE_URL}/devices/{device_id}'
    headers = {'Authorization': f'Bearer {API_KEY}:{API_SECRET}'}
    response = requests.put(url, json=updated_data, headers=headers)
    return response.json()

def install_agent(device_id, agent_data):
    url = f'{BASE_URL}/devices/{device_id}/install_agent'
    headers = {'Authorization': f'Bearer {API_KEY}:{API_SECRET}'}
    response = requests.post(url, json=agent_data, headers=headers)
    return response.json()