import json, urllib.request, urllib.parse

req = urllib.request.Request('http://localhost:8000/api/quiz/generate', headers={'Content-Type': 'application/json'}, data=b'{"tree_type": null, "num_questions": 1, "difficulty": "mixed", "focus_weak": true}')
with urllib.request.urlopen(req) as response:
    quiz = json.loads(response.read())

questions = quiz['questions']
answers = [0] * len(questions)

submit_req = urllib.request.Request('http://localhost:8000/api/quiz/submit', headers={'Content-Type': 'application/json'}, data=json.dumps({"questions": questions, "answers": answers}).encode('utf-8'))
try:
    with urllib.request.urlopen(submit_req) as response:
        print(response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")
