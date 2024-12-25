import os
import frontmatter
import markdown
from datetime import datetime
from jinja2 import Template
from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension
import http.server
import socketserver
import threading
import webbrowser
import shutil

# 创建自定义的Markdown扩展来处理图片大小
class ImgExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(ImgProcessor(), 'img_processor', 15)

class ImgProcessor(Treeprocessor):
    def run(self, root):
        for elem in root.iter('img'):
            # 使用百分比宽度，最大宽度90%
            src = elem.get('src', '')
            alt = elem.get('alt', '')
            # 将img标签的HTML替换为带链接的版本
            elem.set('style', 'width: 90%; max-width: 800px; display: block; margin: 20px auto; cursor: pointer;')
            elem.set('onclick', f'window.open("{src}", "_blank")')
        return root

# HTML template with large text
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <base target="_blank">
</head>
<body style="font-size: 16px; font-family: Arial, sans-serif; width: 90%; max-width: 800px; margin: 0 auto; padding: 5%;">
    <h1 style="font-size: 2em;">{{ title }}</h1>
    
    {% if cover_image %}
    <img src="{{ cover_image }}" alt="Cover Image" style="width: 100%; height: auto; margin: 20px auto;">
    {% endif %}
    
    <p style="font-size: 1em; color: #666;">
        Date: {{ date }}<br>
        Tags: {{ tags|join(', ') }}
    </p>
    
    {% if description %}
    <blockquote style="font-size: 1.2em; font-style: italic; margin: 20px 0; padding: 10px 20px; border-left: 4px solid #ccc;">
        {{ description }}
    </blockquote>
    {% endif %}
    
    <div style="font-size: 1.1em;">
        {{ content }}
    </div>
    
    <hr>
    <p><a href="index.html" target="_self" style="display: inline-block; margin: 20px 0;">← Back to Home</a></p>
</body>
</html>
"""

INDEX_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文件索引</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .directory {
            margin-bottom: 30px;
        }
        .directory-name {
            font-size: 1.5em;
            color: #333;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 2px solid #eee;
        }
        .file-list {
            list-style: none;
            padding-left: 20px;
        }
        .file-item {
            margin: 10px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
            transition: background-color 0.2s;
        }
        .file-item:hover {
            background: #e9ecef;
        }
        .file-link {
            color: #007bff;
            text-decoration: none;
            font-size: 1.1em;
        }
        .file-link:hover {
            text-decoration: underline;
        }
        .file-meta {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
        .breadcrumb {
            margin-bottom: 20px;
            padding: 10px;
            background: #e9ecef;
            border-radius: 4px;
        }
        .search-box {
            width: 100%;
            padding: 10px;
            margin-bottom: 20px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1em;
        }
    </style>
</head>
<body>
    <div class="container">
        <input type="text" class="search-box" id="searchBox" placeholder="搜索文件..." oninput="filterFiles()">
        
        <div class="breadcrumb">
            当前位置: / {% if current_dir %}{{ current_dir }}{% endif %}
        </div>

        {% for dir_name, files in grouped_files.items() %}
        <div class="directory">
            <div class="directory-name">{{ dir_name if dir_name else '根目录' }}</div>
            <ul class="file-list">
                {% for file in files %}
                <li class="file-item">
                    <a href="{{ file.filename }}" class="file-link">{{ file.title }}</a>
                    <div class="file-meta">
                        日期: {{ file.date }}
                        {% if file.tags %}
                        | 标签: {{ file.tags|join(', ') }}
                        {% endif %}
                        {% if file.description %}
                        <div>{{ file.description }}</div>
                        {% endif %}
                    </div>
                </li>
                {% endfor %}
            </ul>
        </div>
        {% endfor %}
    </div>

    <script>
        function filterFiles() {
            const searchText = document.getElementById('searchBox').value.toLowerCase();
            const fileItems = document.getElementsByClassName('file-item');
            
            for (let item of fileItems) {
                const title = item.querySelector('.file-link').textContent.toLowerCase();
                const meta = item.querySelector('.file-meta').textContent.toLowerCase();
                
                if (title.includes(searchText) || meta.includes(searchText)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            }
            
            // 隐藏空的目录
            const directories = document.getElementsByClassName('directory');
            for (let dir of directories) {
                const visibleFiles = dir.querySelectorAll('.file-item[style=""]').length;
                if (visibleFiles === 0) {
                    dir.style.display = 'none';
                } else {
                    dir.style.display = '';
                }
            }
        }
    </script>
</body>
</html>
"""

def process_html_file(filepath):
    """处理HTML文件，提取必要的元数据"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 简单的元数据提取，可以根据需要扩展
    title = os.path.splitext(os.path.basename(filepath))[0]
    date = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d')
    
    return {
        'title': title,
        'date': date,
        'tags': [],
        'description': '',
        'content': content,
        'is_html': True
    }

def process_markdown_file(filepath):
    """处理Markdown文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)
    
    # 创建Markdown转换器实例，添加图片处理扩展
    md = markdown.Markdown(extensions=[ImgExtension()])
    html_content = md.convert(post.content)
    
    return {
        'title': post.get('title', os.path.splitext(os.path.basename(filepath))[0]),
        'date': post.get('date', datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d')),
        'tags': post.get('tags', []),
        'description': post.get('description', ''),
        'cover_image': post.get('cover_image', ''),
        'content': html_content,
        'is_html': False
    }

def scan_directory(source_dir):
    """递归扫描目录，返回所有.md和.html文件"""
    files = []
    for root, _, filenames in os.walk(source_dir):
        for filename in filenames:
            if filename.endswith(('.md', '.html')):
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, source_dir)
                files.append((filepath, rel_path))
    return files

def ensure_directory(filepath):
    """确保文件的目录存在"""
    directory = os.path.dirname(filepath)
    if directory:
        os.makedirs(directory, exist_ok=True)

def group_files_by_directory(posts):
    """将文件按目录分组"""
    grouped = {}
    for post in posts:
        dir_name = os.path.dirname(post['filename'])
        if dir_name not in grouped:
            grouped[dir_name] = []
        grouped[dir_name].append(post)
    return grouped

def copy_directory_structure(source_dir, target_dir):
    """完整复制目录结构和所有文件"""
    for root, dirs, files in os.walk(source_dir):
        # 计算目标目录路径
        relative_path = os.path.relpath(root, source_dir)
        target_root = os.path.join(target_dir, relative_path)
        
        # 创建目标目录
        os.makedirs(target_root, exist_ok=True)
        
        # 复制所有文件
        for file in files:
            source_file = os.path.join(root, file)
            target_file = os.path.join(target_root, file)
            
            # 如果是HTML或MD文件，跳过（这些文件会被单独处理）
            if file.endswith(('.html', '.md')):
                continue
                
            # 复制文件
            shutil.copy2(source_file, target_file)

def clean_directory(directory):
    """安全地清空指定目录的所有内容"""
    if os.path.exists(directory):
        try:
            # 使用shutil.rmtree删除整个目录
            shutil.rmtree(directory, ignore_errors=True)
        except Exception as e:
            print(f"警告：清理目录时出错: {e}")
            # 如果删除失败，尝试重命名原目录
            try:
                old_dir = directory + '_old'
                if os.path.exists(old_dir):
                    shutil.rmtree(old_dir, ignore_errors=True)
                os.rename(directory, old_dir)
            except Exception as e:
                print(f"错误：无法重命名目录: {e}")
                return False
    return True

def generate_blog():
    # 清空并重新创建output目录
    if not clean_directory('output'):
        print("错误：无法清理output目录，请确保没有文件被占用")
        return
    
    os.makedirs('output', exist_ok=True)
    
    # 首先完整复制目录结构和资源文件
    source_dir = 'posts'
    copy_directory_structure(source_dir, 'output')
    
    # Process all markdown and html files
    posts = []
    
    # 扫描所有文件
    files = scan_directory(source_dir)
    
    for filepath, rel_path in files:
        # 确定输出文件路径
        output_path = os.path.join('output', rel_path)
        
        if filepath.endswith('.md'):
            # 处理Markdown文件
            output_path = output_path.replace('.md', '.html')
            post_data = process_markdown_file(filepath)
            
            # 生成HTML文件
            template = Template(TEMPLATE)
            html_output = template.render(**post_data)
            
            # 确保输出目录存在
            ensure_directory(output_path)
            
            # 写入转换后的HTML
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_output)
                
        else:  # .html文件
            # 直接复制HTML文件
            shutil.copy2(filepath, output_path)
            
            # 提取元数据
            post_data = process_html_file(filepath)
        
        # Add to posts list for index page
        posts.append({
            'title': post_data['title'],
            'date': post_data['date'],
            'tags': post_data['tags'],
            'description': post_data.get('description', ''),
            'filename': rel_path.replace('.md', '.html')
        })
    
    # Sort posts by date (newest first)
    posts.sort(key=lambda x: x['date'], reverse=True)
    
    # 按目录分组文件
    grouped_files = group_files_by_directory(posts)
    
    # Generate index page
    template = Template(INDEX_TEMPLATE)
    index_html = template.render(grouped_files=grouped_files, current_dir='')
    with open(os.path.join('output', 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)

def serve(port=8000):
    """启动一个开发服务器"""
    os.chdir('output')  # 切换到输出目录
    
    # 配置服务器
    Handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), Handler)
    
    print(f"开发服务器已启动在 http://localhost:{port}")
    print("按 Ctrl+C 停止服务器")
    
    # 自动打开浏览器
    webbrowser.open(f'http://localhost:{port}')
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        httpd.shutdown()
        httpd.server_close()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'serve':
        # 先生成博客
        generate_blog()
        # 然后启动服务器
        serve()
    else:
        # 只生成博客
        generate_blog()