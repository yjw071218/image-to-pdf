# ImageToPDF · 이미지를 PDF로 엮기

<p align="center"><img src="assets/logo.png" width="220" alt="ImageToPDF 로고"></p>

Windows 탐색기에서 이미지 여러 장을 선택하고, 순서를 정해 하나의 PDF로 저장하는 프로그램입니다. 이미지 변환은 PC 안에서 이루어지며 외부 서버로 업로드하지 않습니다.

## 다운로드 및 설치

**[최신 설치 파일 다운로드](https://github.com/yjw071218/image-to-pdf/releases/latest)**

- 권장: `ImageToPDF-Setup-1.0.0-x64.exe` 실행. 프로그램, 우클릭 메뉴, 시작 메뉴 및 바탕화면 바로가기를 설치합니다.
- 무설치: `ImageToPDF-Portable-1.0.0-x64.zip`을 폴더에 풀고 `ImageToPDF.exe` 실행. 무설치 버전은 우클릭 메뉴를 자동 등록하지 않습니다.
- Windows 10/11 64비트용입니다. Python 설치나 관리자 권한이 필요하지 않습니다.
- 설치 파일은 코드 서명되지 않았습니다. 릴리스의 `SHA256SUMS.txt`로 다운로드 파일의 해시를 확인할 수 있습니다.

## 사용 방법

탐색기에서 이미지 여러 개를 선택 → 우클릭 → **더 많은 옵션 표시** → **이미지를 PDF로 엮기**.

1. 목록에서 이미지를 선택하고 **▲ 위로 / ▼ 아래로** 또는 **Alt+↑ / Alt+↓**로 순서를 정합니다. Ctrl/Shift로 여러 장을 함께 선택할 수 있습니다.
2. **이름순 정렬**은 숫자를 고려해 2, 10 순으로 정렬합니다. **순서 뒤집기**, **선택 제거**, **이미지 추가**도 사용할 수 있습니다.
3. **PDF로 저장…**을 누르고 저장 위치를 선택합니다.

목록 맨 위가 첫 페이지입니다. 원본 이미지 파일은 수정하지 않습니다. 처음 들어오는 이미지 묶음은 이름순으로 추가되며 탐색기에서 클릭한 순서를 보장하지 않으므로 목록에서 최종 순서를 확인하세요.

지원: JPG/JPEG, PNG, BMP, GIF, TIF/TIFF, WebP. GIF와 다중 페이지 TIFF 등은 첫 프레임만 사용합니다. 투명 영역은 흰색 처리하며 EXIF 회전을 적용합니다. 이미지 비율을 유지하고 150dpi 기준의 페이지 크기로 저장합니다. PDF 내부 이미지는 JPEG 품질 95로 압축됩니다.

Windows 11의 기본 간단 메뉴가 아닌 **더 많은 옵션 표시**에 표시됩니다. Shift+F10으로도 이 메뉴를 열 수 있습니다. 정적 탐색기 메뉴는 한 번에 최대 100개 선택을 지원합니다. 그 이상은 앱의 이미지 추가를 이용하세요. 근거: https://learn.microsoft.com/en-us/windows/win32/shell/how-to-employ-the-verb-selection-model

## 설치 위치와 제거

프로그램은 기본적으로 `%LOCALAPPDATA%\Programs\ImageToPDF`에 설치됩니다. 우클릭 메뉴는 현재 사용자에게만 등록됩니다. **Windows 설정 → 앱 → 설치된 앱 → ImageToPDF → 제거**로 프로그램과 메뉴를 제거할 수 있습니다.

여러 탐색기 실행 요청을 모으는 임시 파일은 `%LOCALAPPDATA%\ImageToPDF\inbox`를 사용하며, 요청을 읽으면 삭제합니다. 같은 사용자로 실행한 설치판과 무설치판은 한 창을 공유합니다.

## 소스에서 실행

Python 3.10 이상과 Windows가 필요합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

소스 실행용 우클릭 등록: `.\.venv\Scripts\python.exe setup.py`. 등록 해제: 같은 명령에 `--uninstall` 추가. 소스 등록은 설치판의 메뉴를 대체하므로 설치판을 사용하는 동안에는 실행하지 마세요.

## 설치 파일 빌드

64비트 Python 3.10 이상과 [Inno Setup](https://jrsoftware.org/isinfo.php)이 필요합니다. 이 릴리스는 Python 3.10, PyInstaller 6.22.3, Inno Setup 7.1.0으로 빌드했습니다.

```powershell
.\build.ps1 -InnoCompiler 'C:\path\to\ISCC.exe'
```

빌드 스크립트가 의존성을 설치하고, ICO를 생성하고, 소스 및 패키지 회귀 테스트를 실행한 뒤 `release` 폴더에 설치 EXE, 무설치 ZIP, SHA-256 목록을 생성합니다.

테스트만 실행하려면 프로그램을 닫은 상태에서:

```powershell
.\.venv\Scripts\python.exe app.py --self-test tools\source-report.json
```

검증 항목: PDF 페이지 순서 및 크기, 투명 배경, EXIF 회전, 변환 실패 시 기존 출력 보존, 순서 변경 UI, 미리보기, 중복 제거, 한글/공백 경로를 포함한 20개 프로세스의 단일 창 수신. 탐색기에서 사람이 클릭하는 전체 동작과 다른 PC에서의 호환성은 별도 확인이 필요합니다.

## 라이선스 및 로고

프로젝트는 [MIT 라이선스](LICENSE)로 배포합니다. 번들된 런타임과 라이브러리의 라이선스는 설치 폴더의 `_internal/third-party-licenses`에 포함됩니다. 로고 원본과 생성 프롬프트는 [assets](assets/README.md)에 있습니다.
