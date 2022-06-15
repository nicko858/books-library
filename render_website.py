from jinja2 import Environment, FileSystemLoader, select_autoescape
import json
from livereload import Server
from more_itertools import chunked


def on_reload():
    with open('books.json') as file_handler:
        books = json.load(file_handler)
    books_per_column = len(books) // 2
    chuncked_books = list(chunked(books, books_per_column))
    template = env.get_template('template.html')
    rendered_page = template.render(
        chuncked_books=chuncked_books,
    )
    with open('index.html', 'w', encoding='utf8') as file_handler:
        file_handler.write(rendered_page)
    print("Site reloaded")


if __name__ == '__main__':
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml']),
    )

    server = Server()

    server.watch('template.html', on_reload)

    server.serve(root='.')
