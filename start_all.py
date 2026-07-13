import os
import sys
import time
import zipfile
import urllib.request
import subprocess
from dotenv import load_dotenv, set_key

REDIS_ZIP_URL = "https://github.com/tporadowski/redis/releases/download/v5.0.14.1/Redis-x64-5.0.14.1.zip"

def download_file(url, dest):
    print(f"Downloading {dest} from {url}...")
    urllib.request.urlretrieve(url, dest)
    print("Download complete.")

def setup_redis():
    if not os.path.exists("redis-server.exe"):
        zip_path = "redis.zip"
        download_file(REDIS_ZIP_URL, zip_path)
        print("Extracting Redis...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("redis_temp")
        os.rename(os.path.join("redis_temp", "redis-server.exe"), "redis-server.exe")
        os.rename(os.path.join("redis_temp", "redis.windows.conf"), "redis.windows.conf")
        os.remove(zip_path)
        import shutil
        shutil.rmtree("redis_temp")
    
    print("Starting Redis Server...")
    subprocess.Popen(["redis-server.exe", "redis.windows.conf"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)

import json

def update_env():
    env_file = ".env"
    if not os.path.exists(env_file) and os.path.exists(".env.example"):
        import shutil
        shutil.copy(".env.example", ".env")
        
    load_dotenv()
    
    ngrok_domain = ""
    print("\n*** NGROK SETUP ***")
    print("Checking for a running Ngrok tunnel...")
    
    try:
        req = urllib.request.Request("http://127.0.0.1:4040/api/tunnels")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            for tunnel in data.get('tunnels', []):
                if tunnel['public_url'].startswith('https://'):
                    ngrok_domain = tunnel['public_url']
                    print(f"Auto-detected Ngrok URL: {ngrok_domain}")
                    break
    except Exception as e:
        print("Could not auto-detect Ngrok.")
        print("Please make sure you have run 'ngrok http 8000' in another terminal first.")
        
    if not ngrok_domain:
        ngrok_domain = input("Please paste your exact Ngrok HTTPS URL here: ").strip()
        
    ngrok_domain = ngrok_domain.rstrip("/")
    redirect_uri = f"{ngrok_domain}/callback"
    
    set_key(env_file, "REDIRECT_URI", redirect_uri)
    
    print(f"\n[SUCCESS] Updated .env with REDIRECT_URI={redirect_uri}")
    print("\n>>> IMPORTANT: Ensure this exact Redirect URI is added to your TikTok Developer Portal! <<<\n")
    return redirect_uri

def start_django():
    print("Starting Django server...")
    subprocess.Popen([sys.executable, "manage.py", "runserver"], stdout=sys.stdout, stderr=sys.stderr)

def start_celery():
    print("Starting Celery worker (solo pool for Windows)...")
    subprocess.Popen([sys.executable, "-m", "celery", "-A", "config", "worker", "-l", "info", "--pool=solo"], stdout=sys.stdout, stderr=sys.stderr)

if __name__ == "__main__":
    print("=== TikTok Scheduler Automator (Ngrok Edition) ===")
    
    # Needs python-dotenv installed for set_key
    try:
        import dotenv
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
        
    redirect_uri = update_env()
    setup_redis()
    
    input("Press Enter after you have updated the TikTok Developer portal with your Redirect URI...")
    
    start_django()
    start_celery()
    
    base_url = redirect_uri.replace("/callback", "")
    print("\nAll local services started!")
    print("\n--- NEXT STEPS ---")
    print(f"1. Open a NEW terminal and run your Ngrok tunnel:")
    print(f"   ngrok http --domain={base_url.replace('https://', '')} 8000")
    print(f"2. Visit {base_url} in your browser to authenticate.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping services...")
        print("Close the terminal to terminate all processes.")
