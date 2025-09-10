import requests
session_id='test-session-1234'
payload={'session_id':session_id,'items':[{'product_id':1,'quantity':2}]}
print('update', requests.post('http://localhost:8000/cart/update', json=payload).status_code)
print('get', requests.get(f'http://localhost:8000/cart/{session_id}').status_code)
print(requests.get(f'http://localhost:8000/cart/{session_id}').json())
