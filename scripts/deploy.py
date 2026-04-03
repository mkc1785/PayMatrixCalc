"""
deploy.py — FTP deployment utility for GitHub Actions.
"""
import ftplib, os, io
from urllib.parse import quote

FTP_HOST = os.environ.get("BLUEHOST_HOST", "paymatrixcalc.com")
FTP_USER = os.environ.get("FTP_USERNAME", "tellydos")
FTP_PASS = os.environ.get("FTP_PASSWORD", "")
# no encoding needed for ftplib — but strip any accidental whitespace
FTP_PASS = FTP_PASS.strip()
REMOTE_BASE = "public_html/"

def deploy_file(local_file, remote_subpath=""):
    if not os.path.exists(local_file):
        print(f"  ⚠️ File not found, skipping: {local_file}")
        return
    remote_path = REMOTE_BASE + remote_subpath
    try:
        with ftplib.FTP_TLS(FTP_HOST) as ftp:
            ftp.login(FTP_USER, FTP_PASS)
            ftp.prot_p()
            if remote_subpath:
                try:
                    ftp.mkd(remote_path)
                except:
                    pass
                ftp.cwd(remote_path)
            else:
                ftp.cwd(REMOTE_BASE)
            with open(local_file, 'rb') as f:
                filename = os.path.basename(local_file)
                ftp.storbinary(f'STOR {filename}', f)
        print(f"  ✅ Deployed: {local_file} → {remote_path}")
    except Exception as e:
        raise RuntimeError(f"FTP failed for {local_file}: {e}")

def deploy_files(file_list):
    for local_file, remote_subpath in file_list:
        deploy_file(local_file, remote_subpath)
