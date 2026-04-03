"""
deploy.py — Shared SCP deployment utility.
Import and call deploy_file() or deploy_files() from any script after saving HTML.
"""
import subprocess, os, tempfile

BLUEHOST_USER = os.environ.get("BLUEHOST_USER", "tellydos")
BLUEHOST_HOST = os.environ.get("BLUEHOST_HOST", "sh031.webhostingservices.com")
BLUEHOST_PATH = "public_html/"
SSH_KEY_CONTENT = os.environ.get("BLUEHOST_SSH_KEY", "")

def _get_key_path():
    if not SSH_KEY_CONTENT:
        return r"C:\Users\HP\Downloads\bluehost_paymatrix.pem"
    
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False)
    tmp.write(SSH_KEY_CONTENT)
    tmp.close()
    os.chmod(tmp.name, 0o600)
    
    # Convert OpenSSH format to PEM format
    subprocess.run(
        ["ssh-keygen", "-p", "-m", "PEM", "-f", tmp.name, "-N", "", "-P", ""],
        capture_output=True, text=True
    )
    os.chmod(tmp.name, 0o600)
    return tmp.name

def _scp(local_file, remote_subpath=""):
    key_path = _get_key_path()
    remote = f"{BLUEHOST_USER}@{BLUEHOST_HOST}:{BLUEHOST_PATH}{remote_subpath}"
    cmd = [
    "scp",
    "-i", key_path,
    "-o", "StrictHostKeyChecking=no",
    "-o", "IdentitiesOnly=yes",
    local_file,
    remote
]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"SCP failed for {local_file}: {result.stderr}")
    print(f"  ✅ Deployed: {local_file} → {BLUEHOST_PATH}{remote_subpath}")

def deploy_file(local_file, remote_subpath=""):
    if not os.path.exists(local_file):
        print(f"  ⚠️ File not found, skipping: {local_file}")
        return
    _scp(local_file, remote_subpath)

def deploy_files(file_list):
    for local_file, remote_subpath in file_list:
        deploy_file(local_file, remote_subpath)
