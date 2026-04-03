"""
deploy.py — Shared SCP deployment utility.
Import and call deploy_file() or deploy_files() from any script after saving HTML.
"""

import subprocess, os

BLUEHOST_USER    = "tellydos"
BLUEHOST_HOST    = "sh031.webhostingservices.com"
BLUEHOST_PATH    = "public_html/"
SSH_KEY_PATH     = r"C:\Users\HP\Downloads\bluehost_paymatrix.pem"
SSH_PASSPHRASE   = os.environ.get("BLUEHOST_SSH_PASS", "")

def _scp(local_file, remote_subpath=""):
    """SCP a single file to Bluehost."""
    remote = f"{BLUEHOST_USER}@{BLUEHOST_HOST}:{BLUEHOST_PATH}{remote_subpath}"
    cmd = [
        "scp",
        "-i", SSH_KEY_PATH,
        "-o", "StrictHostKeyChecking=no",
        local_file,
        remote
    ]
    if SSH_PASSPHRASE:
        try:
            cmd = ["sshpass", "-p", SSH_PASSPHRASE] + cmd
        except:
            pass
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"SCP failed for {local_file}: {result.stderr}")
    print(f"  ✅ Deployed: {local_file} → {BLUEHOST_PATH}{remote_subpath}")

def deploy_file(local_file, remote_subpath=""):
    """Deploy a single file. remote_subpath is the folder inside public_html/."""
    if not os.path.exists(local_file):
        print(f"  ⚠️ File not found, skipping: {local_file}")
        return
    _scp(local_file, remote_subpath)

def deploy_files(file_list):
    """
    Deploy multiple files.
    file_list: list of (local_path, remote_subpath) tuples.
    Example: [("blog/post.html", "blog/"), ("sitemap.xml", "")]
    """
    for local_file, remote_subpath in file_list:
        deploy_file(local_file, remote_subpath)
