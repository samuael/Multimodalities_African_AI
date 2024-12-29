import os
import requests
from bs4 import BeautifulSoup
import time

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

TRANSCRIPTS_DIR = "languages/Ghomala/transcripts"
AUDIOS_DIR = "languages/Ghomala/audios"

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

if __name__ == "__main__":
    main()
