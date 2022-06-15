import argparse
import json
from os import makedirs, path
from time import sleep
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests import ConnectionError, HTTPError, ReadTimeout

from book_parser import (BookDoesNotExist, check_for_redirect,
                         download_book_cover, download_book_txt,
                         parse_book_page)

BASE_URL = 'https://tululu.org/'
SLEEP_WHEN_FAIL = 3
BASE_DIR = path.dirname(path.realpath(__file__))
HTTP_TIMEOUT = 3


def get_args(base_dir, target_json_file='books.json'):
    parser = argparse.ArgumentParser()
    parser.add_argument('-book_category_id', nargs='?', type=int, default=55)
    parser.add_argument('-start_page', nargs='?', type=int, default=1)
    parser.add_argument('-end_page', nargs='?', type=int, default=10)
    parser.add_argument('-dest_folder', nargs='?', type=str, default=base_dir)
    parser.add_argument('-skip_imgs', action='store_true')
    parser.add_argument('-skip_txt', action='store_true')
    parser.add_argument('-json_path', nargs='?', type=str, default=path.join(
        base_dir,
        target_json_file,
        ))
    return parser.parse_args()


def parse_books_urls(response):
    soup = BeautifulSoup(response.text, 'lxml')
    books_selector = '#content table a'
    books = soup.select(books_selector)
    book_url_sign = 'b'
    books_urls = []
    for book in books:
        if book_url_sign in book['href']:
            book_url = urljoin(response.url, book['href'])
            books_urls.append(book_url)
    return books_urls


def main():
    args = get_args(BASE_DIR)
    start_page = args.start_page
    end_page = args.end_page
    dest_folder = args.dest_folder
    skip_imgs = args.skip_imgs
    skip_txt = args.skip_txt
    json_path = args.json_path
    book_category_id = args.book_category_id

    books_dir_path = path.join(dest_folder, 'books')
    images_dir_path = path.join(dest_folder, 'images')

    makedirs(books_dir_path, exist_ok=True)
    makedirs(images_dir_path, exist_ok=True)

    first_attemp = True
    book_txt_url = urljoin(BASE_URL, 'txt.php')
    books_urls = []
    while True:
        try:
            for page_num in range(start_page, end_page+1):
                book_category_url = urljoin(BASE_URL, '/l{0}/{1}'.format(
                    book_category_id,
                    page_num,
                    ))
                book_category_response = requests.get(
                    book_category_url,
                    timeout=HTTP_TIMEOUT,
                    )
                book_category_response.raise_for_status()
                check_for_redirect(book_category_response)
                books_urls_per_page = parse_books_urls(book_category_response)
                books_urls.extend(books_urls_per_page)
        except BookDoesNotExist:
            print('Нет коллекции с id={0}!'.format(book_category_url))
            break
        except (HTTPError, ConnectionError, ReadTimeout) as error:
            print('Ошибка при вызове {0}'.format(error.request.url))
            if first_attemp:
                first_attemp = False
                continue
            sleep(SLEEP_WHEN_FAIL)
            continue
        break
    first_attemp = True
    books = []
    for book_url in set(books_urls):
        while True:
            try:
                book_response = requests.get(book_url, timeout=HTTP_TIMEOUT)
                book_response.raise_for_status()
                check_for_redirect(book_response)
                book = parse_book_page(book_response)
                if not skip_imgs:
                    download_book_cover(
                        book['cover_url'],
                        images_dir_path,
                    )
                if not skip_txt:
                    download_book_txt(
                        urljoin(BASE_URL, book_txt_url),
                        book['id'],
                        book['title'],
                        folder=books_dir_path,
                        )
                books.append(book)
            except BookDoesNotExist:
                print('Нет книги с id={0}!'.format(book['id']))
                break
            except (HTTPError, ConnectionError, ReadTimeout) as error:
                print('Ошибка при вызове {0}'.format(error.request.url))
                if first_attemp:
                    first_attemp = False
                    continue
                sleep(SLEEP_WHEN_FAIL)
                continue
            break
    with open(json_path, 'w', encoding='utf-8') as file_handler:
        json.dump(
            books,
            file_handler,
            ensure_ascii=False,
            indent=4,
            )


if __name__ == '__main__':
    main()
