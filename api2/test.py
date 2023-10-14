import requests


with open("Quote-SAGAL.pdf", 'rb') as f:
    r = requests.post("http://localhost:8000/api/v1/tools/coverwhale/quote-reader", files={"file": f})
    print(r.content)