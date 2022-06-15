import argparse
from os import makedirs, path
from time import sleep
from urllib.parse import urljoin, urlparse, urlsplit

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

BASE_URL = 'https://tululu.org/'
SLEEP_WHEN_FAIL = 3
HTTP_TIMEOUT = 3


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
    response = requests.get(url, params={'id': book_id}, timeout=HTTP_TIMEOUT)
    response.raise_for_status()
    check_for_redirect(response)

    sanitized_filename = sanitize_filename('{0}.{1}'.format(
        book_id,
        filename,
        ))
    suffix = '.txt'
    book_path = path.join(folder, '{0}{1}'.format(sanitized_filename, suffix))

    with open(book_path, 'w') as file_handler:
        file_handler.write(response.text)
    return book_path


def download_book_cover(url, folder='images/'):
    response = requests.get(url, timeout=HTTP_TIMEOUT)
    response.raise_for_status()
    check_for_redirect(response)

    file_name = path.basename(urlsplit(url).path)
    sanitized_filename = sanitize_filename(file_name)
    cover_path = path.join(folder, sanitized_filename)

    with open(cover_path, 'wb') as out_file:
        out_file.write(response.content)


def parse_book_page(response):
    soup = BeautifulSoup(response.text, 'lxml')

    download_sign = 'скачать txt'
    table_selector = 'table a'
    table = soup.select(table_selector)

    if not bool([tag for tag in table if download_sign in tag]):
        raise BookDoesNotExist

    parsed_url = urlparse(response.url)
    book_id = int(''.join(filter(str.isdigit, parsed_url.path)))

    target_idx = 0
    title_area = soup.title.text.split(',')
    try:
        title, author = title_area[target_idx].split(' - ')
    except ValueError:
        title_area = soup.title.text.split(' - ')
        title = title_area[target_idx]
        author = title_area[target_idx + 1].split(',')[target_idx]

    book_path = path.join('books', '{0}.{1}.{2}'.format(book_id, title, 'txt'))

    genre_selector = 'span.d_book a'
    genre_tags = soup.select(genre_selector)
    genres = [tag.string for tag in genre_tags]

    comments_selector = 'div.texts span'
    comments = soup.select(comments_selector)
    comments_text = [comment.text for comment in comments]

    book_img_selector = 'table div.bookimage img'
    book_img_src = soup.select_one(book_img_selector)['src']
    book_cover_url = urljoin(response.url, book_img_src)
    img_src = (path.join('images', path.basename(book_img_src)))

    return {
        'id': book_id,
        'title': title,
        'author': author,
        'comments': comments_text,
        'cover_url': book_cover_url,
        'img_src': img_src,
        'book_path': book_path,
        'genres': genres,
    }


def main():
    args = get_args()
    book_start_id = args.start_id
    book_end_id = args.end_id

    base_dir = path.dirname(path.realpath(__file__))
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
            except (requests.HTTPError, requests.ConnectionError) as error:
                print('Ошибка при вызове {0}'.format(error.request.url))
                if first_attemp:
                    first_attemp = False
                    continue
                sleep(SLEEP_WHEN_FAIL)
                continue
            break


if __name__ == '__main__':
    main()
