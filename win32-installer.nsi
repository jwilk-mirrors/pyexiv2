; NSIS installer script for pyexiv2 0.2.

!include MUI.nsh
!include nsDialogs.nsh
!include LogicLib.nsh

Name "pyexiv2 0.2"
OutFile "pyexiv2-0.2-setup.exe"
SetCompressor /SOLID lzma

!define MUI_ICON "art\pyexiv2.ico"
!define MUI_UNICON "art\pyexiv2.ico"

!insertmacro MUI_PAGE_LICENSE "COPYING"
Page custom InstallationOptions InstallationOptionsLeave
!insertmacro MUI_PAGE_INSTFILES

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

!define PYEXIV2_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\pyexiv2-0.2"

Var system_wide
Var user_site

Function .onInit
  Var /GLOBAL python_install_path
  ReadRegStr $python_install_path HKLM Software\Python\PythonCore\2.6\InstallPath ""
  StrCmp $python_install_path "" 0 Continue
  ReadRegStr $python_install_path HKCU Software\Python\PythonCore\2.6\InstallPath ""
  StrCmp $python_install_path "" 0 Continue
  MessageBox MB_OK|MB_ICONSTOP "Unable to locate Python 2.6."
  Quit
  Continue:
    StrCpy $system_wide "$python_install_pathLib\site-packages"
    StrCpy $user_site "$APPDATA\Python\Python26\site-packages"
FunctionEnd

Function InstallationOptions
  !insertmacro MUI_HEADER_TEXT "Installation options" "Choose where to install pyexiv2."

  nsDialogs::Create 1018
  Var /GLOBAL dialog
  Pop $dialog
  ${If} $dialog == error
    Abort
  ${EndIf}

  ${NSD_CreateRadioButton} 0 0 100% 24u "System wide ($system_wide)"
  Var /GLOBAL rb1
  Pop $rb1
  ${NSD_SetState} $rb1 ${BST_CHECKED}

  ${NSD_CreateRadioButton} 0 34 100% 24u "User site ($user_site)"
  Var /GLOBAL rb2
  Pop $rb2

  nsDialogs::Show
FunctionEnd

Function InstallationOptionsLeave
  ${NSD_GetState} $rb1 $0
  ${If} $0 == ${BST_CHECKED}
    StrCpy $INSTDIR $system_wide
  ${Else}
    StrCpy $INSTDIR $user_site
  ${EndIf}
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
  WriteRegStr HKLM ${PYEXIV2_KEY} "DisplayName" "pyexiv2 0.2"
  WriteRegStr HKLM ${PYEXIV2_KEY} "DisplayVersion" "0.2"
  WriteRegStr HKLM ${PYEXIV2_KEY} "DisplayIcon" "$INSTDIR\pyexiv2-0.2-uninstaller.exe"
  WriteRegStr HKLM ${PYEXIV2_KEY} "UninstallString" "$INSTDIR\pyexiv2-0.2-uninstaller.exe"
  WriteRegDWORD HKLM ${PYEXIV2_KEY} "NoModify" 1
  WriteRegDWORD HKLM ${PYEXIV2_KEY} "NoRepair" 1
SectionEnd

Section "Uninstall"
  Delete $INSTDIR\libexiv2python.py*
  RMDir /r $INSTDIR\pyexiv2

  DeleteRegKey HKLM ${PYEXIV2_KEY}

  Delete $INSTDIR\pyexiv2-0.2-uninstaller.exe
SectionEnd

