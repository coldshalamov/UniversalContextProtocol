import sys
sys.path.insert(0, r'D:\GitHub\Telomere\UniversalContextProtocol\local\src\ucp_mvp')

with open('__init__.py', 'r') as f:
    content = f.read()
    content = content.replace('__all__', '__all__')
    content = content.replace('__version__', '__version__')
    
with open('__init__.py', 'w') as fw:
    fw.write(content)

print("Fixed __init__.py")
