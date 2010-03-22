!include MUI.nsh

Name "pyexiv2 0.2"
OutFile "pyexiv2-0.2-setup.exe"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "COPYING"
; Need for a custom page here to choose wether to install for all users or only
; for the current user.
!insertmacro MUI_PAGE_INSTFILES
;!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "English"

Var python_install_path

Section "pyexiv2"
  ReadRegStr $python_install_path HKLM Software\Python\PythonCore\2.6\InstallPath ""
  ;DetailPrint "Python is installed at: $python_install_path"
  ; FIXME: if python was installed for the current user only, its installation
  ; path will be found at HKEY_CURRENT_USER\SOFTWARE\Python\PythonCore\2.6\InstallPath
  SetOutPath $python_install_path\Lib\site-packages
  File build\libexiv2python.pyd
  SetOutPath $python_install_path\Lib\site-packages\pyexiv2
  File src\pyexiv2\__init__.py
  File src\pyexiv2\metadata.py
  File src\pyexiv2\exif.py
  File src\pyexiv2\iptc.py
  File src\pyexiv2\xmp.py
  File src\pyexiv2\utils.py
SectionEnd

