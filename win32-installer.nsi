!include MUI.nsh

Name "pyexiv2 0.2"
OutFile "pyexiv2-0.2-setup.exe"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "COPYING"
; Need for a custom page here to choose wether to install for all users or only
; for the current user.
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "English"

Section "pyexiv2"
  ; FIXME: un-hardcode INSTDIR.
  StrCpy $INSTDIR "C:\Python26\Lib\site-packages"
  SetOutPath $INSTDIR
  File build\libexiv2python.pyd
  SetOutPath $INSTDIR\pyexiv2
  File src\pyexiv2\__init__.py
  File src\pyexiv2\metadata.py
  File src\pyexiv2\exif.py
  File src\pyexiv2\iptc.py
  File src\pyexiv2\xmp.py
  File src\pyexiv2\utils.py
SectionEnd

