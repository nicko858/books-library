  #!/bin/bash
  
  git clone https://github.com/nicko858/books-library.git
  cd books-library
  python3 -m venv ./venv
  . venv/bin/activate
  pip install -r requirements.txt
  python book_category_parser.py
  python render_website.py