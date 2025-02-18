import os
import csv
import json
import time
import requests
from bs4 import BeautifulSoup

# from selenium import webdriver
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Constants
# Structure of books and chapters of the Bible 
BOOKS_AND_CHAPTERS = {
    "MAT": 28,
    "MRK": 16,
    "LUK": 24,
    "JHN": 21,
    "ACT": 28,
    "ROM": 16,
    "1CO": 16,
    "2CO": 13,
    "GAL": 6,
    "EPH": 6,
    "PHP": 4,
    "COL": 4,
    "1TH": 5,
    "2TH": 3,
    "1TI": 6,
    "2TI": 4,
    "TIT": 3,
    "PHM": 1,
    "HEB": 13,
    "JAS": 5,
    "1PE": 5,
    "2PE": 3,
    "1JN": 5,
    "2JN": 1,
    "3JN": 1,
    "JUD": 1,
    "REV": 22,
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
}

TRANSCRIPTS_DIR = "languages/Ghomala/Supervised/transcripts"
TRANSCRIPTS_UNSUPERVISED_DIR = "languages/Ghomala/Unsupervised/transcripts"
AUDIOS_DIR = "languages/Ghomala/Supervised/audios"
AUDIOS_UNSUPERVISED_DIR = "languages/Ghomala/Unsupervised/audios"
CSV_FILE = "languages/Ghomala/Assets/jw_ghomala.csv"
BASE_URL_JW = "https://www.jw.org/"

# Create the directory if it doesn't exist
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
os.makedirs(AUDIOS_DIR, exist_ok=True)

def generate_url(content_type, book, chapter):
    """
    Generate the URL for a given content type, book, and chapter.

    Args:
        content_type (str): Type of content ("text" or "audio").
        book (str): The book identifier (e.g., "MAT").
        chapter (int): The chapter number.

    Returns:
        str: The generated URL.
    """
    base_url = "https://www.bible.com"
    if content_type == "text":
        return f"{base_url}/bible/907/{book}.{chapter}.NTGOMALA"
    elif content_type == "audio":
        return f"{base_url}/audio-bible/907/{book}.{chapter}.NTGOMALA"
    else:
        raise ValueError(f"Invalid content type: {content_type}")


def download_and_structure_transcripts(book, chapter):
    """
    Downloads and structures the transcript for a given book and chapter.
    
    Args:
        book (str): The code of the book (e.g., "MAT" for Matthew).
        chapter (int): The chapter number.
    
    Description:
        - Fetches the webpage containing the transcript for the specified book and chapter.
        - Parses the HTML to extract sections and verses.
        - Structures the content into a readable format and saves it as a text file.
    """

    url = generate_url("text", book, chapter)
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        
        soup = BeautifulSoup(response.content, "html.parser")

        sections = soup.find_all("span", class_="ChapterContent_heading__xBDcs")
        paragraphs = soup.find_all("div", class_="ChapterContent_p__dVKHb")

        structured_content = []

        for section in sections:
            section_title = section.get_text(strip=True)
            section_paragraphs = []

            for para in paragraphs:
                verses = para.find_all("span", class_="ChapterContent_content__RrUqA")
                paragraph_text = " ".join(verse.get_text(strip=True) for verse in verses)
                if paragraph_text.strip():
                    section_paragraphs.append(paragraph_text)

            if section_title and section_paragraphs:
                structured_content.append(f"## {section_title}\n" + "\n".join(section_paragraphs))

        if structured_content:
            with open(f"{TRANSCRIPTS_DIR}/{book}_{chapter}.txt", "w", encoding="utf-8") as file:
                file.write("\n\n".join(structured_content))
            print(f"Structured transcript saved for {book} {chapter}")
        else:
            print(f"No content found for {book} {chapter}")
    else:
        print(f"Error for {book} {chapter}: {response.status_code}")


def download_audio(book, chapter):
    """
    Downloads the audio file for a given book and chapter.
    
    Args:
        book (str): The code of the book (e.g., "MAT" for Matthew).
        chapter (int): The chapter number.
    
    Description:
        - Fetches the webpage containing the audio for the specified book and chapter.
        - Extracts the audio source URL and downloads the file.
        - Saves the audio file in the designated directory.
    """
    
    url = generate_url("audio", book, chapter)
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        
        soup = BeautifulSoup(response.content, "html.parser")
        audio_tag = soup.find("audio", id="dataman-audio")
        
        if audio_tag and audio_tag.get("src"):
            audio_url = audio_tag["src"]
            print(f"Downloading audio for {book} {chapter} from {audio_url}...")
            
            audio_response = requests.get(audio_url, stream=True)
            if audio_response.status_code == 200:
                file_path = f"{AUDIOS_DIR}/{book}_{chapter}.mp3"
                with open(file_path, "wb") as file:
                    for chunk in audio_response.iter_content(chunk_size=1024):
                        file.write(chunk)
                print(f"Audio saved for {book} {chapter} at {file_path}")
            else:
                print(f"Error downloading audio for {book} {chapter}: {audio_response.status_code}")
        else:
            print(f"No <audio> tag found for {book} {chapter}")
    else:
        print(f"Error for {book} {chapter}: {response.status_code}")

def main():
    """
    Main function to orchestrate the download and structuring of transcripts and audio files.
    
    Description:
        - Iterates through all books and chapters defined in BOOKS_AND_CHAPTERS.
        - Downloads and structures transcripts for each chapter.
        - Downloads audio files for each chapter.
        - Includes a short pause between requests to avoid server overload.
    """
    
    for book, chapters in BOOKS_AND_CHAPTERS.items():
        for chapter in range(1, chapters + 1):
            print(f"Processing {book} chapter {chapter}...")
            
            try:
                download_and_structure_transcripts(book, chapter)
            except Exception as e:
                print(f"Error extracting transcript: {e}")
            
            try:
                download_audio(book, chapter)
            except Exception as e:
                print(f"Error downloading audio: {e}")
            
            time.sleep(1)
# ______________________________________________________________________________________________________________________________________________________________________________#

def extract_all_publication_links(url, visited_pages=None):
    """
    Extract all publication links from a webpage, including links on paginated pages.

    Args:
        url (str): The starting URL of the webpage to scrape.
        visited_pages (set): A set of already visited URLs to prevent loops.

    Returns:
        list: A list of publication links extracted from the webpage.
    """
    if visited_pages is None:
        visited_pages = set()

    # Prevent visiting the same URL multiple times
    if url in visited_pages:
        return []

    visited_pages.add(url)
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract publication links under <h3> tags
        pub_links = set()
        pubs_section = soup.find(id='pubsViewResults')
        if not pubs_section:
            print(f"No 'pubsViewResults' section found at {url}.")
            return []

        for h3 in pubs_section.find_all('h3'):
            anchor = h3.find('a', href=True)
            if anchor:
                pub_links.add(anchor['href'])  # Add to set

        # Extract pagination links
        next_main_pub = []
        links_section = pubs_section.find('div', class_='links')
        if links_section:
            for link in links_section.find_all('a', href=True):
                next_main_pub.append(link['href'])
                    
        # Recursively fetch links from pagination
        for next_page in next_main_pub:
            full_next_page_url = requests.compat.urljoin(BASE_URL_JW, next_page)
            pub_links.update(extract_all_publication_links(full_next_page_url, visited_pages))

        return list(pub_links)

    except requests.exceptions.RequestException as e:
        print(f"Error during the request to {url}: {e}")
        return []

def save_transcript(content, filepath):
    """
    Save text content to a file in the transcripts directory.

    Args:
        content (str): The text content to save.
        filepath (str): The path of the file to save the content to.
    """
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Transcript saved: {filepath}")
    except Exception as e:
        print(f"Error saving transcript {filepath}: {e}")

def process_publication_links(publication_links):
    """
    Process a list of publication links to extract additional links and detail page content.

    Args:
        publication_links (list): A list of publication links to process.

    Returns:
        list: A list of new links discovered during processing.
    """
    new_links = []
    for link in publication_links:
        try:
            format_link = requests.compat.urljoin(BASE_URL_JW, link)
            response = requests.get(format_link)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Check for card sections containing additional links
            cards_section = soup.find("div", class_="toc")
            if cards_section:
                for card in cards_section.find_all("a", href=True):
                    new_links.append(requests.compat.urljoin(BASE_URL_JW, card["href"]))
                print(f"New links added from {format_link}")
            else:
                # process_publication_detail_page(format_link)
                save_links_in_csv(format_link)

        except requests.RequestException as e:
            print(f"Error during request to {link}: {e}")

    return new_links

def save_links_in_csv(format_link):
    """
    Saves a link in the jw_ghomala.csv file depending on its nature.

    Args:
        format_link (str): The link to save.
        audio_url (str or None): Associated audio link, if available.
    """
    
    # Create CSV file if needed with columns defined
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["Supervised_link", "Supervised_audio", "Unsupervised_link"])
        if not file_exists:
            writer.writeheader()

        audio_url = get_specific_request_url(format_link)
        if audio_url:  
            writer.writerow({"Supervised_link": format_link, "Supervised_audio": audio_url, "Unsupervised_link": ""})
        else:  
            writer.writerow({"Supervised_link": "", "Supervised_audio": "", "Unsupervised_link": format_link})
    

def get_specific_request_url(url):
    """
    Retrieve a specific request URL matching a target prefix using Selenium.

    Args:
        url (str): The webpage URL to analyze.

    Returns:
        str: The MP3 URL, or None if not found.
    """
    target_prefix = "https://b.jw-cdn.org/apis/pub-media/GETPUBMEDIALINKS"
    driver = webdriver.Chrome()

    try:
        driver.get(url)
        for request in driver.requests:
            if request.url.startswith(target_prefix):
                # return request.url
                try:
                    audio_res = requests.get(request.url)
                    
                    if audio_res.status_code != 200:
                        raise ValueError(f"API request failed with status {audio_res.status_code}: {audio_res.text}")
                    
                    audio_json = audio_res.json()
                    # mp3_url = audio_json["files"]["GHM"]["MP3"][0]["file"]["url"]
                    
                    # Safely navigate through the JSON structure
                    if not isinstance(audio_json, dict):
                        raise ValueError(f"Invalid JSON format: {audio_json}")
                    
                    mp3_url = (
                        audio_json.get("files", {})
                        .get("GHM", {})
                        .get("MP3", [{}])[0]
                        .get("file", {})
                        .get("url")
                    )
                    
                    if not mp3_url:
                        raise ValueError(f"MP3 URL not found in the JSON API {request.url}.")
                    
                    return mp3_url
                except Exception as e:
                    print(f"Error extracting audio URL: {e}")
                    
    finally:
        driver.quit()
    return None

def download_jw_audio(mp3_url, audio_title):
    """
    Download an audio file from mp3 url.

    Args:
        mp3_url (str): The URL of the MP3.
        audio_title (str): The title to use for the saved audio file.
    """
    try:
        audio_response = requests.get(mp3_url, stream=True)
        audio_response.raise_for_status()

        file_path = os.path.join(AUDIOS_DIR, f"Jw_{audio_title.replace(' ', '_')}.mp3") 
        with open(file_path, "wb") as file:
            for chunk in audio_response.iter_content(chunk_size=1024):
                file.write(chunk)
        print(f"Audio saved for {audio_title} at {file_path}")

    except (KeyError, IndexError, ValueError, requests.RequestException) as e:
        print(f"Error extracting or downloading audio: {e}")

def process_publication_detail_page(url, audio_url=None):
    """
    Process a publication detail page to save text content and download audio files.

    Args:
        url (str): The detail page URL to process.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract title and content
        title_tag = soup.find(class_="onPageTitle")
        title = title_tag.get_text(strip=True) if title_tag else "Untitled"

        content_tag = soup.find(class_="docSubContent")
        content = content_tag.get_text(strip=True) if content_tag else "No content found"

        # Save transcript
        transcript_filename = f"Jw_{title.replace(' ', '_')}.txt"
        filepath = os.path.join(TRANSCRIPTS_DIR, transcript_filename) if audio_url else os.path.join(TRANSCRIPTS_UNSUPERVISED_DIR, transcript_filename)
        if content != "No content found":
            save_transcript(content, filepath)

        # Download audio if available
        if audio_url:
            download_jw_audio(audio_url, title)

    except requests.RequestException as e:
        print(f"Error during the request to {url}: {e}")


def download_jw_data():
    """
    Main function to manage the download process of JW data.
    If the CSV file exists, it processes each row.
    If the CSV file does not exist, it creates the file using the scraping process and then processes it.
    """
    if os.path.exists(CSV_FILE):
        print(f"CSV file '{CSV_FILE}' exists. Processing its rows...")
        
        # Read and process each row in the existing CSV file
        with open(CSV_FILE, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                url_sup = row.get("Supervised_link") 
                url_unsup = row.get("Unsupervised_link")
                audio_url = row.get("Supervised_audio")
                
                if url_sup:
                    process_publication_detail_page(url_sup, audio_url)
                else:
                    process_publication_detail_page(url_unsup)
    else:
        
        print(f"CSV file '{CSV_FILE}' does not exist. Creating it...")
        start_url = "https://www.jw.org/bbj/two/mbounwanye/"
        publication_links = extract_all_publication_links(start_url)
        print("All Publication Links:", publication_links)
        
        while publication_links:
            new_links = process_publication_links(publication_links)
            publication_links = new_links  # Update with the new links
        
        # Process the newly created CSV file
        download_jw_data()

if __name__ == "__main__":
    #__________________________ To download New Testamant Audio_______________________#
    
    # main()

    #_________________________To Download Audio and text from BASE_URL_JW______________#
    
    download_jw_data()
    
        
        
        