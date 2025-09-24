# KPMG 2025 정부지원사업 추천 시스템

## 📋 프로젝트 개요
스타트업을 위한 정부지원사업 맞춤 추천 시스템의 MVP 버전입니다.

## 🚀 주요 기능

### 1. 맞춤 추천
- **회사 선택**: 드롭다운에서 회사 선택 (기본값: 대박드림스)
- **자동 추천**: 회사 선택 시 자동으로 추천 결과 표시
- **필터링**: 전체 공고 / 활성 공고 / 신규 공고 필터
- **추천 점수**: 0-100점 기준 추천 점수 표시

### 2. 신규 공고 알림
- **실시간 알림**: Supabase 연동으로 실제 데이터 기반
- **알림 현황**: 총 알림 수, 확인된 알림, 이번 달 공고 수
- **마감 임박**: 마감일이 임박한 공고 목록

### 3. 로드맵 생성
- **월별 분포**: 막대 그래프로 월별 공고 수 시각화
- **월별 상세보기**: 각 월을 클릭하여 해당 월의 공고 목록 확인
- **실제 데이터**: yyyymmdd ~ yyyymmdd 형식의 실제 날짜 데이터만 사용

## 🛠️ 기술 스택
- **Frontend**: Streamlit
- **Backend**: Supabase
- **Database**: PostgreSQL (Supabase)
- **Visualization**: Plotly
- **Language**: Python 3.13

## 🚀 배포 방법

### Streamlit Cloud 배포
1. 이 저장소를 GitHub에 업로드
2. [Streamlit Cloud](https://share.streamlit.io/)에서 새 앱 생성
3. GitHub 저장소 연결
4. 환경변수 설정:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
5. 메인 파일: `app.py`

### 로컬 실행
```bash
# 패키지 설치
pip install -r requirements.txt

# 환경변수 설정 (.env 파일 생성)
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# 앱 실행
streamlit run app.py
```

## 📊 데이터베이스 구조

### Supabase 테이블
- `alpha_companies_final`: 기업 정보
- `recommend_final`: 추천 공고 데이터

### 데이터 처리 로직
- **월별 데이터**: yyyymmdd ~ yyyymmdd 형식만 사용
- **추천 점수**: 0-100점 스케일로 정규화
- **실시간 연동**: Supabase와 완전 연동

## 🎯 주요 특징
- **실시간 데이터**: Supabase와 완전 연동
- **사용자 친화적**: 직관적인 UI/UX
- **반응형**: 자동 업데이트 및 필터링
- **시각화**: 월별 분포 차트 및 상세 정보

## 📝 버전 정보
- **버전**: MVP 1.0
- **최종 업데이트**: 2025-09-25
- **상태**: 배포 준비 완료

---
*KPMG 2025 정부지원사업 추천 시스템 MVP*
