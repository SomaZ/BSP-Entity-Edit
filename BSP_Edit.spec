# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
		('data_frame.py', '.'),
		('edit_menu.py', '.'),
		('file_menu.py', '.'),
		('format_menu.py', '.'),
		('help_menu.py', '.'),
		('lighting_frame.py', '.'),
		('ogl_baking.py', '.'),
		('ogl_camera.py', '.'),
		('ogl_fbo.py', '.'),
		('ogl_frame.py', '.'),
		('ogl_objects.py', '.'),
		('ogl_shader.py', '.'),
		('ogl_state.py', '.'),
		('render_menu.py', '.'),
		('text_frame.py', '.'),
		('pyidtech3lib', 'pyidtech3lib/')
		],
    hiddenimports=[
		'numpy',
		'pyopengltk',
		'ctypes'
		],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BSP Edit',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
