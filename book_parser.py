import argparse
from os import makedirs, path
from time import sleep
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

BASE_URL = 'https://tululu.org/'
SLEEP_WHEN_FAIL = 3


class BookDoesNotExist(Exception):
    pass


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('start_id', nargs='?', type=int, default=1)
    parser.add_argument('end_id', nargs='?', type=int, default=10)
    return parser.parse_args()


def check_for_redirect(response):
    if response.history:
        raise BookDoesNotExist


def download_book_txt(url, book_id, filename, folder='books/'):
    response = requests.get(url, params={'id': book_id})
    response.raise_for_status()
    sanitized_filename = sanitize_filename('{0}.{1}'.format(book_id, filename))
    suffix = '.txt'
    book_path = path.join(folder, '{0}{1}'.format(sanitized_filename, suffix))
    with open(book_path, 'w') as file_handler:
        file_handler.write(response.text)
    return book_path


def download_book_cover(url, folder='images/'):
    response = requests.get(url)
    response.raise_for_status()
    file_name = path.basename(urlsplit(url).path)
    sanitized_filename = sanitize_filename(file_name)
    cover_path = path.join(folder, sanitized_filename)
    with open(cover_path, 'wb') as out_file:
        out_file.write(response.content)


def parse_book_page(response):
    soup = BeautifulSoup(response.text, 'lxml')
    download_sign = 'скачать txt'
    table = soup.find('table', attrs={'class': 'd_book'})
    if not bool([tag for tag in table.findAll('a') if download_sign in tag]):
        raise BookDoesNotExist
    target_idx = 0
    title, author = soup.title.text.split(',')[target_idx].split(' - ')
    comments = soup.findAll('div', attrs={'class': 'texts'})
    comments_text = [comment.find('span').text for comment in comments]
    bookimage_tag = table.find('div', attrs={'class': 'bookimage'})
    book_cover_url = urljoin(response.url, bookimage_tag.find('img')['src'])
    genre_tags = soup.find('span', attrs={'class': 'd_book'}).find('a')['title']
    genres = genre_tags.split(' - ')[target_idx].split(',')
    return {
        'title': title,
        'author': author,
        'comments': comments_text,
        'cover_url': book_cover_url,
        'genres': genres,
    }


if __name__ == '__main__':
    args = get_args()
    base_dir = path.dirname(path.realpath(__file__))
    book_start_id = args.start_id
    book_end_id = args.end_id
    books_dir_path = path.join(base_dir, 'books')
    images_dir_path = path.join(base_dir, 'images')
    makedirs(books_dir_path, exist_ok=True)
    makedirs(images_dir_path, exist_ok=True)
    first_attemp = True
    for book_id in range(book_start_id, book_end_id+1):
        while True:
            book_url = urljoin(BASE_URL, '/b{0}/'.format(book_id))
            book_txt_url = urljoin(BASE_URL, 'txt.php')
            try:
                book_response = requests.get(book_url)
                book_response.raise_for_status()
                check_for_redirect(book_response)
                book = parse_book_page(book_response)
                download_book_cover(
                    book['cover_url'],
                    images_dir_path,
                )
                download_book_txt(
                    urljoin(BASE_URL, book_txt_url),
                    book_id,
                    book['title'],
                    folder=books_dir_path,
                    )
            except BookDoesNotExist:
                print('Нет книги с id={0}!'.format(book_id))
                break
            except (requests.HTTPError, requests.ConnectionError):
                print('Ошибка при вызове ресурса {0}'.format(book_url))
                print('Ошибка при вызове {0}'.format(book_url))
                if first_attemp:
                    first_attemp = False
                    continue
                sleep(SLEEP_WHEN_FAIL)
                continue
            break
