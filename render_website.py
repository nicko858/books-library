from jinja2 import Environment, FileSystemLoader, select_autoescape
import json
from livereload import Server
from more_itertools import chunked
from math import ceil
from os import path, makedirs

BASE_DIR = path.dirname(path.realpath(__file__))


def on_reload():
    with open('books.json') as file_handler:
        books = json.load(file_handler)
    books_per_page = 20
    books_per_column = 10
    pages_count = ceil(len(books) / books_per_page)
    chuncked_books = list(chunked(books, books_per_page))
    pages_path = path.join(BASE_DIR, 'pages')
    makedirs(pages_path, exist_ok=True)
    for idx, books in enumerate(chuncked_books):
        page_path = path.join(pages_path, 'index{0}.html'.format(idx))
        template = env.get_template('template.html')
        chuncked_books = list(chunked(books, books_per_column))
        rendered_page = template.render(
            pages_count=pages_count,
            current_page_num=idx,
            chuncked_books=chuncked_books,
            pages_path=pages_path,
        )
        with open(page_path, 'w', encoding='utf8') as html:
            html.write(rendered_page)
    print("Site reloaded")


if __name__ == '__main__':
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml']),
    )

    server = Server()

    server.watch('template.html', on_reload)

    server.serve(root='.')
