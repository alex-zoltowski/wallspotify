# -*- mode: python ; coding: utf-8 -*-
from os.path import join, abspath


block_cipher = None

dir_path = abspath('.')

a = Analysis([join(dir_path, 'wallspotify.py')],
             pathex=[dir_path],
             binaries=[],
             datas=[(join(dir_path, 'assets', 'icon.png'), join('.', 'assets')),
                    (join(dir_path, 'assets', 'icon.ico'), join('.', 'assets'))],
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
          name='WallSpotify',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False, icon=join(dir_path, 'assets', 'icon.ico') )
app = BUNDLE(exe,
             name='WallSpotify.app',
             icon=join(dir_path, 'assets', 'icon.icns'),
             console=True,
             bundle_identifier=None,
             info_plist={
                'NSHighResolutionCapable': 'True'
            } )