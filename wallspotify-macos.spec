# -*- mode: python -*-

block_cipher = None


a = Analysis(['wallspotify.py'],
             pathex=['/Users/angie/Development/wallspotify'],
             binaries=[],
             datas=[('icon.png', './')],
             hiddenimports=['requests'],
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
          name='wallspotify',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False , icon='icon.icns')
app = BUNDLE(exe,
             name='wallspotify.app',
             icon='icon.icns',
             bundle_identifier=None,
             info_plist={
                'NSHighResolutionCapable': 'True'
            } )
