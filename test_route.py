import requests

# Test normal route
res = requests.post("http://localhost:8000/route", json={
    "start_station": "PEOPLE'S SQUARE",
    "end_station": "XUJIAHUI",
    "metric": "duration",
    "excluded_lines": []
})
print("NORMAL:", res.json()['path'][0]['name'], "->", res.json()['path'][-1]['name'])

# Test exclusion correctly blocking
res = requests.post("http://localhost:8000/route", json={
    "start_station": "HENGSHAN ROAD", # Only on Line 1
    "end_station": "CENTURY AVENUE",
    "metric": "duration",
    "excluded_lines": [1] # Exclude Line 1
})
print("EXCLUDED START STATION:", res.json())

# Test complex route with exclusions
res = requests.post("http://localhost:8000/route", json={
    "start_station": "PEOPLE'S SQUARE",
    "end_station": "CENTURY AVENUE",
    "metric": "duration",
    "excluded_lines": [2] # Usually take line 2, now force another way
})
print("AVOID LINE 2:")
for n in res.json()['path']:
    print(n['line_id'], n['name'])
