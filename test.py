import requests


with open("test3.pdf", 'rb') as f:
    r = requests.post("http://localhost:8000/api/v1/pdf-to-json", files={"file": f})
    print(r.content)