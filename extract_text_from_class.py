import requests
from bs4 import BeautifulSoup

def extract_text_from_class(url: str, class_name: str) -> str:
    """
    Extracts all text content from the first element with the given class name on the page at the specified URL.
    Args:
        url (str): The URL of the web page.
        class_name (str): The class name of the element to extract text from.
    Returns:
        str: The extracted text content, or an empty string if not found.
    """
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    section = soup.find(class_=class_name)
    if section:
        return section.get_text(separator='\n', strip=True)
    return ""

if __name__ == "__main__":
    # Example usage
    url = "https://herp.careers/careers/companies/geofla/jobs/iQu0qGpUWV_d"
    class_name = "bg-white flex flex-col gap-3 px-4 sm:px-6 py-2 sm:py-6"  # Use the full class string
    text = extract_text_from_class(url, class_name)
    print(text)
