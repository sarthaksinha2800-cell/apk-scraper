from utils import setup_session, load_config, save_config
import requests
import os
from github import Github
import base64

class APKDownloader:
    def __init__(self, github_token=None):
        self.session = setup_session()
        self.gh = Github(github_token) if github_token else None
    
    def download_apk(self, url, filename):
        """Download APK file"""
        try:
            print(f"Downloading APK from {url}")
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            # Ensure downloads directory exists
            os.makedirs('downloads', exist_ok=True)
            
            filepath = os.path.join('downloads', filename)
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Downloaded: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error downloading APK: {e}")
            return None
    
    def upload_to_release(self, repo_name, filepath, release_tag, version):
        """Upload APK to GitHub release"""
        if not self.gh:
            print("GitHub token not provided")
            return False
        
        try:
            repo = self.gh.get_repo(repo_name)
            
            # Check if release exists
            try:
                release = repo.get_release(release_tag)
                # Delete existing assets
                for asset in release.get_assets():
                    asset.delete_asset()
            except:
                # Create new release
                release = repo.create_git_release(
                    tag=release_tag,
                    name=f"{os.path.basename(filepath).replace('.apk', '')} {version}",
                    message=f"Auto-updated APK - Version {version}",
                    draft=False,
                    prerelease=False
                )
            
            # Upload APK
            with open(filepath, 'rb') as f:
                release.upload_asset(
                    path=filepath,
                    label=os.path.basename(filepath),
                    content_type='application/vnd.android.package-archive'
                )
            
            print(f"Uploaded {filepath} to release {release_tag}")
            return True
            
        except Exception as e:
            print(f"Error uploading to release: {e}")
            return False
    
    def update_apk_list(self, apk_name, new_version):
        """Update APK list with new version"""
        config = load_config()
        
        for apk in config['tracked_apks']:
            if apk['name'] == apk_name:
                apk['current_version'] = new_version
                break
        
        save_config(config)
        print(f"Updated {apk_name} to version {new_version}")
