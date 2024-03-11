## SHP to GeoJson 추출 프로그램

### 실행파일 생성과정

```shell
pyinstaller ./app.spec
```

### GeoJson 추출과정

1. [지오서비스웹 아카이브 접속](https://www.geoservice.co.kr/)
2. 회원가입 및 로그인
3. 아카이브 > 소유자명(gizmo) > 최신행정구역도 쉐이프파일 다운로드
4. GeoJson-Extractor 실행
5. 시도/시군구/읍면동 쉐이프파일 업로드
6. 다운로드 경로 설정
7. 실행 버튼 클릭

![program](https://github.com/abdc06/geojson-extractor/assets/113388660/226130b3-1976-47c5-b41e-4775ef0af2e4)
