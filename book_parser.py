import requests
from os import makedirs, path


def make_book_dir():
    base_dir = path.dirname(path.realpath(__file__))
    books_dir = path.join(base_dir, 'books')
    try:
        makedirs(books_dir, exist_ok=True)
        return(books_dir)
    except OSError as error:
        print(error)


if __name__ == '__main__':
    url = 'https://tululu.org/txt.php?id={0}'
    books_count = 10
    books_dir = make_book_dir()
    for book_id in range(1, books_count+1):
        response = requests.get(url.format(book_id))
        response.raise_for_status
        book_text = response.text
        with open(path.join(books_dir, 'id{0}.txt'.format(book_id)), 'w') as file_handler:
            file_handler.write(book_text)
