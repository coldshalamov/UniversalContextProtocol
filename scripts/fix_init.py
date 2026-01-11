with open('__init__.py', 'r') as f:
    content = f.read()
    content = content.replace('__all__', '__all__')
with open('__init__.py', 'w') as fw:
    fw.write(content)
