#!/usr/bin/env python3
import argparse
from scraper import GetModsApkScraper
from downloader import APKDownloader
from utils import load_config
import os

def main():
    parser = argparse.ArgumentParser(description='APK Scraper for GetModsApk')
    parser.add_argument('--auto', action='store_true', help='Auto process all APKs')
    parser.add_argument('--manual', action='store_true', help='Manual download')
    parser.add_argument('--url', help='APK URL for manual download')
    parser.add_argument('--tag', help='Release tag for manual download')
    parser.add_argument('--name', help='APK name for manual download')
    
    args = parser.parse_args()
    
    github_token = os.getenv('GITHUB_TOKEN')
    repo_name = os.getenv('GITHUB_REPOSITORY')
    
    scraper = GetModsApkScraper()
    downloader = APKDownloader(github_token)
    
    if args.auto:
        print("Running auto scraper...")
        config = load_config()
        
        for apk in config['tracked_apks']:
            print(f"\nProcessing {apk['name']}...")
            
            # Check current version
            current_version = scraper.get_current_version(apk['base_url'])
            if current_version and current_version != apk['current_version']:
                print(f"New version found: {current_version} (was {apk['current_version']})")
                
                # Get download link
                download_url = scraper.get_download_links(apk['base_url'])
                if download_url:
                    filename = f"{apk['name'].replace(' ', '-').lower()}-{current_version}.apk"
                    filepath = downloader.download_apk(download_url, filename)
                    
                    if filepath and github_token:
                        downloader.upload_to_release(
                            repo_name, 
                            filepath, 
                            apk['release_tag'], 
                            current_version
                        )
                        downloader.update_apk_list(apk['name'], current_version)
            else:
                print(f"No update available for {apk['name']}")
    
    elif args.manual and args.url and args.tag and args.name:
        print("Running manual download...")
        download_url = scraper.get_download_links(args.url)
        
        if download_url:
            current_version = scraper.get_current_version(args.url)
            filename = f"{args.name.replace(' ', '-').lower()}-{current_version}.apk"
            filepath = downloader.download_apk(download_url, filename)
            
            if filepath and github_token:
                downloader.upload_to_release(
                    repo_name,
                    filepath,
                    args.tag,
                    current_version
                )

if __name__ == "__main__":
    main()
