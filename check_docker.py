import os
import subprocess
import shutil
import sys

def check_docker():
    print("🔍 AI Chatbot Docker Diagnostic Tool\n")
    
    # 1. Check if docker is in PATH
    docker_path = shutil.which("docker")
    if docker_path:
        print(f"✅ Docker found in PATH: {docker_path}")
        try:
            version = subprocess.check_output(["docker", "--version"]).decode().strip()
            print(f"   Version: {version}")
        except:
            print("   ⚠️  Found binary but could not execute it.")
    else:
        print("❌ Docker NOT found in standard PATH.")

    # 2. Check common Mac paths
    common_paths = [
        "/usr/local/bin/docker",
        "/usr/bin/docker",
        "/opt/homebrew/bin/docker",
        "/Applications/Docker.app/Contents/Resources/bin/docker"
    ]
    
    found_any = False
    for path in common_paths:
        if os.path.exists(path):
            print(f"📍 Found potential Docker binary at: {path}")
            found_any = True
            
    # 3. Check if Docker.app exists
    app_path = "/Applications/Docker.app"
    if os.path.exists(app_path):
        print(f"🏢 Docker Desktop App is installed at {app_path}")
    else:
        print("🏢 Docker Desktop App NOT found in /Applications.")

    # 4. Summary & Advice
    print("\n--- Summary ---")
    if docker_path:
        print("Everything looks good! You can run: docker-compose up --build")
    elif found_any:
        print("Docker is installed but not linked to your terminal.")
        print("Try running this command to fix it:")
        print(f"sudo ln -s {common_paths[0]} /usr/local/bin/docker")
    else:
        print("Docker might not be fully installed.")
        print("1. Please open Docker Desktop and finish the 'Setup' if prompted.")
        print("2. If not installed, get it from: https://www.docker.com/products/docker-desktop/")

if __name__ == "__main__":
    check_docker()
