# Pure HTML Blog Generator

A simple static blog generator that creates pure HTML pages from Markdown files, without CSS or JavaScript.

## Features

- Large, readable text by default
- Markdown support
- Frontmatter for metadata
- Support for:
  - Titles
  - Links
  - Tags
  - Descriptions
  - Cover images
  - Dates

## Setup

1. Install Python 3.7 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Create Markdown files in the `posts` directory with the following frontmatter format:
   ```markdown
   ---
   title: Your Post Title
   date: YYYY-MM-DD
   tags: [tag1, tag2]
   description: A brief description of your post
   cover_image: URL to your cover image (optional)
   ---

   Your post content in Markdown format...
   ```

2. Run the generator:
   ```bash
   python generate.py
   ```

3. The generated HTML files will be in the `output` directory:
   - Individual post pages as `[post-name].html`
   - An index page as `index.html`

## Directory Structure

```
.
├── posts/              # Your Markdown blog posts
├── output/            # Generated HTML files
├── generate.py        # The blog generator script
└── requirements.txt   # Python dependencies
``` 