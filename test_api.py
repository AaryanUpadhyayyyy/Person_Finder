import requests

try:
    url = 'http://localhost:8000/api/scan'
    files = {'file': ('test.jpg', b'dummy_image_data', 'image/jpeg')}
    data = {'serpapi_key': 'dummy_key'}
    response = requests.post(url, files=files, data=data)
    print(f'Status: {response.status_code}')
    print(f'Response: {response.text}')
except Exception as e:
    print(f'Error: {e}')
