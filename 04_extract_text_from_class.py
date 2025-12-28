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
    ids = ["job-overview", "qualifications", "compensation", "company-overview"]
    texts = []
    for id_name in ids:
        elem = soup.find(id=id_name)
        if elem:
            # job-match-analysisを含む子要素を除外
            job_match = elem.find(id="job-match-analysis")
            if job_match:
                job_match.extract()
            # company-overview内の特定divを除外
            if id_name == "company-overview":
                exclude_div = elem.find('div', class_="flex flex-col gap-4")
                if exclude_div:
                    exclude_div.extract()
            texts.append(elem.get_text(separator='\n', strip=True))
    # 追加で更新日時のテキストも抽出
    update_elems = soup.find_all('p', class_="scroll-m-20 text-sm text-pretty text-gray-600")
    for elem in update_elems:
        texts.append(elem.get_text(strip=True))
    if texts:
        return '\n\n'.join(texts)
    return ""

if __name__ == "__main__":
    # Example usage
    url = "https://herp.careers/careers/companies/luchegroup/jobs/ixIlWaegVFkd"
    # class_name is no longer needed
    text = extract_text_from_class(url, None)
    print(text)
