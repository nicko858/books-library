from os import makedirs, path

import requests


def make_book_dir(books_dir):
    try:
        makedirs(books_dir, exist_ok=True)
    except OSError as error:
        print(error)
        return
    return books_dir


def check_for_redirect(respose):
    if response.history:
        raise requests.HTTPError


if __name__ == '__main__':
    base_url = 'https://tululu.org/txt.php?id={0}'
    base_dir = path.dirname(path.realpath(__file__))
    books_dir = path.join(base_dir, 'books')
    books_count = 10
    book_start_id = 1
    books_dir = make_book_dir(books_dir)
    if not books_dir:
        exit('Не удалось создать директорию для книг!')
    for book_id in range(book_start_id, books_count+1):
        response = requests.get(base_url.format(book_id))
        book_text = response.text
        book_path = path.join(books_dir, 'id{0}.txt'.format(book_id))
        try:
            check_for_redirect(response)
        except requests.HTTPError:
            continue
        with open(book_path, 'w') as file_handler:
            file_handler.write(book_text)
