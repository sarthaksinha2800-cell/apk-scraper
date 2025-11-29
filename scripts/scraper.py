from utils import setup_session, extract_version_info
from bs4 import BeautifulSoup
import re
import time

class GetModsApkScraper:
    def __init__(self):
        self.session = setup_session()
        self.base_domain = "https://getmodsapk.com"
    
    def get_download_links(self, base_url):
        """Get download links following the multi-step process"""
        try:
            # Step 1: Navigate to base URL
            print(f"Step 1: Accessing {base_url}")
            response = self.session.get(base_url)
            response.raise_for_status()
            
            # Step 2: Go to download page
            download_page_url = base_url.rstrip('/') + '/download/'
            print(f"Step 2: Accessing download page {download_page_url}")
            response = self.session.get(download_page_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Step 3: Find the latest version download section
            # Look for download buttons or links
            download_buttons = soup.find_all('a', href=True, string=re.compile(r'download', re.I))
            
            # Also look for buttons with download-related text
            for button in soup.find_all(['a', 'button']):
                if button.get_text(strip=True).lower() in ['download', 'begin download', 'download now']:
                    href = button.get('href', '')
                    if href and '/download/' in href:
                        download_id_url = self.base_domain + href if href.startswith('/') else href
                        print(f"Step 3: Found download link: {download_id_url}")
                        
                        # Step 4: Get final download page
                        print(f"Step 4: Accessing final download page {download_id_url}")
                        final_response = self.session.get(download_id_url)
                        final_response.raise_for_status()
                        
                        final_soup = BeautifulSoup(final_response.content, 'html.parser')
                        
                        # Find direct APK download link
                        apk_link = self.extract_direct_apk_link(final_soup, download_id_url)
                        if apk_link:
                            return apk_link
            
            # Alternative extraction method
            return self.alternative_extraction(soup, base_url)
            
        except Exception as e:
            print(f"Error getting download links: {e}")
            return None
    
    def extract_direct_apk_link(self, soup, page_url):
        """Extract direct APK download link from final page"""
        # Method 1: Look for .apk links
        apk_links = soup.find_all('a', href=re.compile(r'\.apk$', re.I))
        for link in apk_links:
            href = link.get('href', '')
            if href:
                return href if href.startswith('http') else self.base_domain + href
        
        # Method 2: Look for download buttons with data attributes
        download_buttons = soup.find_all(['a', 'button'], 
                                       attrs={'href': True, 'data-download': True})
        for button in download_buttons:
            href = button.get('href', '')
            if href and '.apk' in href.lower():
                return href if href.startswith('http') else self.base_domain + href
        
        # Method 3: Extract from JavaScript or meta tags
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string:
                apk_match = re.search(r'https?://[^"\']*\.apk[^"\']*', script.string, re.I)
                if apk_match:
                    return apk_match.group(0)
        
        print(f"Could not find APK link on {page_url}")
        return None
    
    def alternative_extraction(self, soup, base_url):
        """Alternative method to extract download links"""
        # Look for version lists or dropdowns
        version_sections = soup.find_all('div', class_=re.compile(r'version|download', re.I))
        
        for section in version_sections:
            links = section.find_all('a', href=re.compile(r'download/\d+/'))
            for link in links:
                href = link.get('href', '')
                if href:
                    download_url = self.base_domain + href if href.startswith('/') else href
                    print(f"Trying alternative download URL: {download_url}")
                    
                    try:
                        response = self.session.get(download_url)
                        response.raise_for_status()
                        
                        alt_soup = BeautifulSoup(response.content, 'html.parser')
                        apk_link = self.extract_direct_apk_link(alt_soup, download_url)
                        if apk_link:
                            return apk_link
                    except Exception as e:
                        print(f"Error with alternative URL: {e}")
                        continue
        
        return None
    
    def get_current_version(self, base_url):
        """Get current version from the website"""
        try:
            response = self.session.get(base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for version in page content
            version_patterns = [
                r'v?(\d+\.\d+\.\d+)',
                r'version\s*[:]?\s*(\d+\.\d+\.\d+)',
                r'ver\.?\s*(\d+\.\d+\.\d+)'
            ]
            
            page_text = soup.get_text()
            for pattern in version_patterns:
                match = re.search(pattern, page_text, re.I)
                if match:
                    return match.group(1)
            
            # Look in meta tags or specific elements
            version_elements = soup.find_all(['span', 'div', 'p'], 
                                           string=re.compile(r'v?\d+\.\d+\.\d+'))
            for element in version_elements:
                version = extract_version_info(element.get_text())
                if version:
                    return version
            
            return None
            
        except Exception as e:
            print(f"Error getting current version: {e}")
            return None
