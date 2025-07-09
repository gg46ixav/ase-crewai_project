import json
import os
import subprocess
import requests

from ase.crew import CrewaiAgents

API_URL = "http://localhost:8081/task/index/"

LOG_FILE = "results.log"

def handle_task(index):
    """
    Handle a specific task from the crew.
    """
    api_url = f"{API_URL}{index}"
    repo_dir = os.path.join("/home/theo/Uni/ASE/repos/", f"repo_{index}")
    start_dir = os.getcwd()

    response = requests.get(api_url)
    if response.status_code != 200:
        raise Exception(f"Invalid Task API response: {response.status_code}")
    testcase = response.json()
    prompt = testcase["Problem_statement"]
    git_clone = testcase["git_clone"]
    fail_tests = json.loads(testcase.get("FAIL_TO_PASS", "[]"))
    pass_tests = json.loads(testcase.get("PASS_TO_PASS", "[]"))
    instance_id = testcase["instance_id"]
    parts = git_clone.split("&&")
    clone_part = parts[0].strip()
    checkout_part = parts[-1].strip() if len(parts) > 1 else None
    repo_url = clone_part.split()[2]
    commit_hash = checkout_part.split()[-1] if checkout_part else "main"

    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    if not os.path.exists(repo_dir):
        subprocess.run(["git", "clone", repo_url, repo_dir], check=True, env=env)
    else:
        print(f"Repo {repo_dir} already exists – skipping clone.")

    #subprocess.run(["git", "checkout", commit_hash], cwd=repo_dir, check=True, env=env)

    if repo_dir and prompt:
        inputs = {
            'repository': repo_dir,
            'prompt': prompt
        }

    try:
       output = CrewaiAgents(working_directory=repo_dir).crew().kickoff(inputs=inputs)
    except:
        pass

    test_payload = {
        "instance_id": instance_id,
        "repoDir": f"/repos/repo_{index}",  # mount with docker
        "FAIL_TO_PASS": fail_tests,
        "PASS_TO_PASS": pass_tests
    }

    res = requests.post("http://localhost:8082/test", json=test_payload)

    print(res.json())
    os.chdir(start_dir)
    result_raw = res.json().get("harnessOutput", "{}")
    result_json = json.loads(result_raw)
    if not result_json:
        with open(LOG_FILE, "a", encoding="utf-8") as log:
            log.write(f"\n--- TESTCASE {index} ---\n")
            log.write(f"No data in harnessOutput – possible evaluation error or empty result\n")
            return
    instance_id = next(iter(result_json))
    tests_status = result_json[instance_id]["tests_status"]
    fail_pass_results = tests_status["FAIL_TO_PASS"]
    fail_pass_total = len(fail_pass_results["success"]) + len(fail_pass_results["failure"])
    fail_pass_passed = len(fail_pass_results["success"])
    pass_pass_results = tests_status["PASS_TO_PASS"]
    pass_pass_total = len(pass_pass_results["success"]) + len(pass_pass_results["failure"])
    pass_pass_passed = len(pass_pass_results["success"])

    # Log results
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"\n--- TESTCASE {index} ---\n")
        log.write(f"FAIL_TO_PASS passed: {fail_pass_passed}/{fail_pass_total}\n")
        log.write(f"PASS_TO_PASS passed: {pass_pass_passed}/{pass_pass_total}\n")
    print(f"Test case {index} completed.")


def run():
    for i in range(1,31):
        handle_task(i)

if __name__ == "__main__":
    run()