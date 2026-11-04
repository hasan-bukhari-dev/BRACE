"""Small dependency-free Windows launcher guard; never install globally."""
import struct,sys
def main():
    base=str(sys.base_prefix).lower()
    if not ((3,11)<=sys.version_info[:2]<(3,14)) or struct.calcsize('P')!=8:
        print('BRACE needs CPython 3.11-3.13, 64-bit. Release wheelhouse tested on 3.11 x64.');return 1
    if sys.implementation.name!='cpython' or any(x in base for x in ('espressif','idf-python')):
        print('Select a standard CPython installation, not ESP-IDF Python.');return 1
    print('Python '+sys.version.split()[0]+' x64 selected; project dependencies stay in .venv.');return 0
if __name__=='__main__':raise SystemExit(main())
