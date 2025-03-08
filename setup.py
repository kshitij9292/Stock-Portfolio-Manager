import sys
from cx_Freeze import setup, Executable
build_options = {
    'packages': ['requests', 'bs4', 'tkinter', 'sqlite3', 'certifi'],
    'excludes': [],
    'include_files': []
}
base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable(
        'Min.py',
        base=base,
        target_name='StockPortfolioManager.exe',
        icon='SPM.ico'
    )
]
setup(
    name='Stock Portfolio Manager',
    version='1.0',
    description='Manage your stock portfolio',
    options={'build_exe': build_options},
    executables=executables
)