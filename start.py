import subprocess
import sys
import os
import shutil

def run_command(command, cwd=None):
    """Running a shell command with real-time output."""
    try:
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            shell=False,
            cwd=cwd
        )
        # Stream output
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        # Check for errors
        if process.returncode != 0:
            err = process.stderr.read()
            print(f"Error executing command: {command}\n{err}")
            sys.exit(process.returncode)
            
    except Exception as e:
        print(f"Failed to execute {command}: {e}")
        sys.exit(1)

def main():
    print("🚀 Initializing Best Execution Analyzer Setup (Python)...")

    # 1. Check for uv
    if not shutil.which("uv"):
        print("📦 'uv' not found. Installing via pip...")
        run_command([sys.executable, "-m", "pip", "install", "uv"])
    else:
        print("✅ 'uv' is already installed.")

    # 2. Create Virtual Environment
    if not os.path.exists(".venv"):
        print("🛠️  Creating virtual environment with uv...")
        run_command(["uv", "venv"])
    else:
        print("✅ Virtual environment (.venv) already exists.")

    # 3. Install Dependencies
    print("⬇️  Installing dependencies...")
    # Use the venv's python or uv pip interface
    # uv pip install -r requirements.txt --python .venv
    # Windows/Linux path handling for venv python
    venv_python = os.path.join(".venv", "bin", "python")
    if sys.platform == "win32":
        venv_python = os.path.join(".venv", "Scripts", "python.exe")
    
    # We can use 'uv pip install' targeting the environment
    run_command(["uv", "pip", "install", "-r", "requirements.txt"])

    # 4. Run Application
    print("✨ Setup complete! Launching Dashboard...")
    print("----------------------------------------------------------------")
    
    # We execute streamlit using the VENV's python executable to ensure it runs in the venv
    # Format: .venv/bin/python -m streamlit run src/frontend/app.py
    
    app_path = os.path.join("src", "frontend", "app.py")
    
    try:
        # Replaces current process with the streamlit process
        if sys.platform == "win32":
             subprocess.run([venv_python, "-m", "streamlit", "run", app_path], check=True)
        else:
            os.execv(venv_python, [venv_python, "-m", "streamlit", "run", app_path])
            
    except Exception as e:
        print(f"Failed to launch app: {e}")

if __name__ == "__main__":
    main()
