from os import makedirs, path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

BASE_URL = 'https://tululu.org/'


class BookDoesNotExist(Exception):
    """Воспроизводится, когда нет возможности скачать книгу."""
    pass


def make_book_dir(books_dir):
    """Функция для создания директории.
    Args:
        books_dir (str): Путь к целевой директории.
    Returns:
        (str): Путь к целевой директории
    """
    makedirs(books_dir, exist_ok=True)
    return books_dir


def check_for_redirect(response):
    """Функция для проверки http-ответа на наличие событий redirect.

    Args:
        response (requests.models.Response): Объект полученный,
        при выполнении запроса requests.get() (http-ответ)
    Returns:
        bool: Был ли redirect ?
    """
    if response.history:
        raise BookDoesNotExist


def is_possible_to_download(response):
    """Функция для проверки возможности скачивания
    файла исходя из данных http-ответа.

    Args:
        response (requests.models.Response): Объект полученный,
        при выполнении запроса requests.get() (http-ответ)
    Returns:
        Ничего не возвращает. Только вызывает BookDoesNotExist
        если не выполняется условие.
    """
    target_str = 'скачать txt'
    soup = BeautifulSoup(response.text, 'lxml')
    table = soup.find('table', attrs={'class': 'd_book'})
    if not bool([tag for tag in table.findAll('a') if target_str in tag]):
        raise BookDoesNotExist


def get_author_and_title(response):
    """Функция для извлечения строк автор
       и название книги из html-страницы.
    Args:
        response (requests.models.Response): Объект полученный,
        при выполнении запроса requests.get() (http-ответ)
    Returns:
        tuple: название книги, автор книги
    """
    soup = BeautifulSoup(response.text, 'lxml')
    target_idx = 0
    title, author = soup.title.text.split(',')[target_idx].split(' - ')
    return (title, author)


def download_book_txt(url, book_id, filename, folder='books/'):
    """Функция для скачивания текстовых файлов(книг).

    Args:
        url (str): Cсылка на ресурс, с которого будем качать.
        book_id (int): id книги, которую хочется скачать
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    response = requests.get(url, params={'id': book_id})
    response.raise_for_status()
    sanitized_filename = sanitize_filename('{0}.{1}'.format(book_id, filename))
    suffix = '.txt'
    book_path = path.join(folder, sanitized_filename + suffix)
    with open(book_path, 'w') as file_handler:
        file_handler.write(response.text)
    return book_path


if __name__ == '__main__':
    base_dir = path.dirname(path.realpath(__file__))
    books_count = 10
    book_start_id = 1
    books_dir = make_book_dir(path.join(base_dir, 'books'))
    for book_id in range(book_start_id, books_count+1):
        book_info_url = urljoin(BASE_URL, '/b{0}/'.format(book_id))
        book_data_url = urljoin(BASE_URL, 'txt.php')
        try:
            book_info_response = requests.get(book_info_url)
            book_info_response.raise_for_status()
            check_for_redirect(book_info_response)
            is_possible_to_download(book_info_response)
            title, author = get_author_and_title(book_info_response)
            download_book_txt(
                urljoin(BASE_URL, book_data_url),
                book_id,
                title,
                folder=books_dir,
                )
        except BookDoesNotExist:
            print('Нет книги с id={0}!'.format(book_id))
        except (requests.HTTPError, requests.ConnectionError):
            print('Ошибка при вызове ресурса {0}'.format(book_info_url))
