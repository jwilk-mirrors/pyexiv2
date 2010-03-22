!include MUI.nsh

Name "pyexiv2 0.2"
OutFile "pyexiv2-0.2-setup.exe"

;!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "COPYING"
; Need for a custom page here to choose wether to install for all users or only
; for the current user.
!insertmacro MUI_PAGE_INSTFILES
;!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "English"

Var python_install_path

Function .onInit
  ReadRegStr $python_install_path HKLM Software\Python\PythonCore\2.6\InstallPath ""
  StrCmp $python_install_path "" 0 Continue
  ReadRegStr $python_install_path HKCU Software\Python\PythonCore\2.6\InstallPath ""
  StrCmp $python_install_path "" 0 Continue
  MessageBox MB_OK|MB_ICONSTOP "Unable to locate Python 2.6."
  Quit
  Continue:
FunctionEnd

Section "pyexiv2"
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

