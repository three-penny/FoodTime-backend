import urllib.request, json

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYTRlMDU4NmMtNTZkNi00MzMzLWFmMzUtOTIzMTk1YzdkOGZhIiwiYWNjb3VudCI6ImFkbWluIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzgxMDIzMzcxLCJpYXQiOjE3ODA5MzY5NzF9.rORhAVJovLxKBiuAT1RTuvQLPJKe0qd8HxPCyfnFaqQ"

req = urllib.request.Request("http://localhost:5000/api/v1/submissions", headers={"Authorization": f"Bearer {token}"})
resp = urllib.request.urlopen(req, timeout=10)
print(resp.read().decode())
