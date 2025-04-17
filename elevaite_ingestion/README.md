.
├── README.md
├── __init__.py
├── __pycache__
│   └── config.cpython-310.pyc
├── config.py
├── ingest_pipeline.py
├── input_data
│   └── sample_file.docx
├── logs
│   └── pipeline.log
├── output_data
│   └── sample_file.md
├── parsers
│   ├── __init__.py
│   ├── __pycache__
│   │   ├── __init__.cpython-310.pyc
│   │   ├── __init__.cpython-39.pyc
│   │   ├── docx_parser.cpython-310.pyc
│   │   ├── xlsx_parser.cpython-310.pyc
│   │   └── xlsx_parser.cpython-39.pyc
│   ├── docx_parser.py
│   ├── pdf_parser.py
│   ├── url_parser.py
│   └── xlsx_parser.py
├── requirements.txt
├── structured_data
│   ├── __init__.py
│   ├── __pycache__
│   │   ├── __init__.cpython-310.pyc
│   │   ├── json_writer.cpython-310.pyc
│   │   └── markdown_writer.cpython-310.pyc
│   ├── json_writer.py
│   └── markdown_writer.py
├── tests
│   ├── __init__.py
│   ├── test_ingest_pipeline.py
│   ├── test_parsers.py
│   └── test_tools.py
├── tools
│   ├── __init__.py
│   ├── __pycache__
│   │   ├── __init__.cpython-310.pyc
│   │   └── __init__.cpython-39.pyc
│   ├── custom_tools
│   │   └── __init__.py
│   └── standard_tools
│       ├── __init__.py
│       ├── __pycache__
│       │   ├── __init__.cpython-310.pyc
│       │   ├── __init__.cpython-39.pyc
│       │   ├── docling.cpython-310.pyc
│       │   ├── markitdown.cpython-310.pyc
│       │   └── markitdown.cpython-39.pyc
│       ├── crawl4ai.py
│       ├── docling.py
│       ├── llamaparse.py
│       └── markitdown.py
├── utils
│   ├── __init__.py
│   ├── __pycache__
│   │   ├── __init__.cpython-310.pyc
│   │   └── logger.cpython-310.pyc
│   ├── file_utils.py
│   └── logger.py
└── resource.txt