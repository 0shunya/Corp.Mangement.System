import requests

url = "http://127.0.0.1:5000/checkin"
headers = {"Content-Type": "application/json"}
data = {"user_id": "user123"}

response = requests.post(url, headers=headers, json=data)
print("Check In Response:", response.json())

url = "http://127.0.0.1:5000/checkout"
data = {"user_id": "user123"}

response = requests.post(url, headers=headers, json=data)
print("Check Out Response:", response.json())

url = "http://127.0.0.1:5000/task_completion_report"
data = {"user_id": "user123", "task_details": "Completed task A"}

response = requests.post(url, headers=headers, json=data)
print("Task Completion Response:", response.json())

url = "http://127.0.0.1:5000/attendance_report"
response = requests.get(url)
print("Attendance Report Response:", response.json())
