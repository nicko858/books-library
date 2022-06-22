import argparse
import json
from functools import partial
from math import ceil
from os import makedirs, path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked

BASE_DIR = path.dirname(path.realpath(__file__))


def get_args(base_dir, books_json_file='books.json'):
    parser = argparse.ArgumentParser()
    parser.add_argument('-is_dev_mode', action='store_true')
    parser.add_argument(
        '-books_json_path',
        nargs='?',
        type=str,
        default=path.join(
            base_dir,
            books_json_file,
        )
    )
    return parser.parse_args()


def generate_books_library(
    pages_count,
    chuncked_books,
    pages_path,
    debug_msg=None,
):
    books_per_column = 10
    last_chuncked_element = len(chuncked_books)
    for idx, books in enumerate(chuncked_books, start=1):
        is_first_page = idx == 1
        is_last_page = idx == last_chuncked_element
        next_page = idx + 1
        previous_page = idx - 1
        page_path = path.join(pages_path, 'index{0}.html'.format(idx))
        template = env.get_template('template.html')
        chuncked_books = list(chunked(books, books_per_column))
        rendered_page = template.render(
            pages_count=pages_count,
            current_page_num=idx,
            chuncked_books=chuncked_books,
            pages_path=pages_path,
            next_page=next_page,
            previous_page=previous_page,
            is_first_page=is_first_page,
            is_last_page=is_last_page,
        )
        with open(page_path, 'w', encoding='utf8') as html:
            html.write(rendered_page)
    if debug_msg:
        print(debug_msg)


if __name__ == '__main__':
    args = get_args(BASE_DIR)
    is_dev_mode = args.is_dev_mode
    books_json_path = args.books_json_path

    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml']),
    )

    with open(books_json_path) as file_handler:
        books = json.load(file_handler)

    books_per_page = 20
    pages_count = ceil(len(books) / books_per_page)
    chuncked_books = list(chunked(books, books_per_page))

    pages_path = path.join(BASE_DIR, 'pages')
    makedirs(pages_path, exist_ok=True)

    if is_dev_mode:
        debug_msg = 'Site reloaded'
        server = Server()

        server.watch('template.html', partial(
            generate_books_library,
            chuncked_books=chuncked_books,
            pages_count=pages_count,
            pages_path=pages_path,
            debug_msg=debug_msg,
        ))

        server.serve(root='.')

    generate_books_library(pages_count, chuncked_books, pages_path)
