import requests
from bs4 import BeautifulSoup
import os

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}
def get_soup(url):
    response = requests.get(url, headers=headers)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup
    
def latest(num):
    url = os.getenv('url')
    url = f"{url}page/{num}"
    soup = get_soup(url)
    div_tags = soup.find_all('div', class_='tdb_module_loop td_module_wrap td-animation-stack td-cpt-post')
    result_list = []  # Empty list to store the information

    for div in div_tags:
        image_tag = div.find('span', class_='entry-thumb td-thumb-css')
        if image_tag:
            image_url = image_tag['data-img-url']

        h3_tag = div.find('h3', class_='entry-title td-module-title')
        if h3_tag:
            a_tag = h3_tag.find('a')
            if a_tag:
                title = a_tag.text
                link = a_tag['href']
                result_list.append({"title": title, "url": link, "img": image_url})  # Append title, link, and image URL together as a dictionary to the list

    return result_list
