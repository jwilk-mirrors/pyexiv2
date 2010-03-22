; NSIS installer script for pyexiv2 0.2.

!include MUI.nsh

Name "pyexiv2 0.2"
OutFile "pyexiv2-0.2-setup.exe"

!define MUI_ICON "art\pyexiv2.ico"
!define MUI_UNICON "art\pyexiv2.ico"

;!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "COPYING"
; Need for a custom page here to choose wether to install for all users or only
; for the current user ($APPDATA\Python\Python26\site-packages)
!insertmacro MUI_PAGE_INSTFILES
;!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Function .onInit
  Var /GLOBAL python_install_path
  ReadRegStr $python_install_path HKLM Software\Python\PythonCore\2.6\InstallPath ""
  StrCmp $python_install_path "" 0 Continue
  ReadRegStr $python_install_path HKCU Software\Python\PythonCore\2.6\InstallPath ""
  StrCmp $python_install_path "" 0 Continue
  MessageBox MB_OK|MB_ICONSTOP "Unable to locate Python 2.6."
  Quit
  Continue:
    StrCpy $INSTDIR "$python_install_path\Lib\site-packages"
FunctionEnd

Section "pyexiv2"
  SetOutPath $INSTDIR
  File build\libexiv2python.pyd

  SetOutPath $INSTDIR\pyexiv2
  File src\pyexiv2\__init__.py
  File src\pyexiv2\metadata.py
  File src\pyexiv2\exif.py
  File src\pyexiv2\iptc.py
  File src\pyexiv2\xmp.py
  File src\pyexiv2\utils.py

  WriteUninstaller $INSTDIR\pyexiv2-0.2-uninstaller.exe
  Var /GLOBAL key
  StrCpy $key "Software\Microsoft\Windows\CurrentVersion\Uninstall\pyexiv2-0.2"
  WriteRegStr HKLM $key "DisplayName" "pyexiv2 0.2"
  WriteRegStr HKLM $key "DisplayVersion" "0.2"
  WriteRegStr HKLM $key "UninstallString" "$INSTDIR\pyexiv2-0.2-uninstaller.exe"
  WriteRegDWORD HKLM $key "NoModify" 1
  WriteRegDWORD HKLM $key "NoRepair" 1
SectionEnd

Section "Uninstall"
  Delete $INSTDIR\libexiv2python.py*
  RMDir /r $INSTDIR\pyexiv2

  StrCpy $key "Software\Microsoft\Windows\CurrentVersion\Uninstall\pyexiv2-0.2"
  DeleteRegKey HKLM $key

  Delete $INSTDIR\pyexiv2-0.2-uninstaller.exe
SectionEnd

