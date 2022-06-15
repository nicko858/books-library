from jinja2 import Environment, FileSystemLoader, select_autoescape
import json


if __name__ == '__main__':
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml']),
    )
    with open('books.json') as file_handler:
        books = json.load(file_handler)
    template = env.get_template('template.html')
    rendered_page = template.render(
        books=books,
    )
    with open('index.html', 'w', encoding='utf8') as file_handler:
        file_handler.write(rendered_page)