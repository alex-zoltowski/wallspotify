# -*- mode: python ; coding: utf-8 -*-
from os.path import join, abspath


block_cipher = None

dir_path = abspath('.')

a = Analysis([join(dir_path, 'wallspotify-windows.py')],
             pathex=[dir_path],
             binaries=[],
             datas=[(join(dir_path, 'assets\\icon.png'), '.\\assets')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='wallspotify-windows',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
