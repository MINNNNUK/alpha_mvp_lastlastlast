import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import json
import os
import sys
import re

# 상위 디렉토리의 모듈 import를 위해 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Supabase 클라이언트 import
from supabase_client import supabase_client

# Supabase 기반 추천 시스템 사용

# 페이지 설정
st.set_page_config(
    page_title="스타트업 정부지원사업 추천 시스템",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
    .info-message {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #bee5eb;
    }
</style>
""", unsafe_allow_html=True)

def load_company_list():
    """Supabase에서 회사 목록을 로드하는 함수"""
    try:
        # Supabase 연결 테스트
        if hasattr(supabase_client, 'test_connection'):
            connection_ok = supabase_client.test_connection()
            if not connection_ok:
                st.warning("⚠️ Supabase 연결에 실패했습니다. 샘플 데이터를 사용합니다.")
                return get_sample_companies()
        
        # Supabase에서 회사 목록 가져오기
        companies = supabase_client.get_companies()
        
        if companies:
            st.success(f"✅ {len(companies)}개 회사 데이터를 Supabase에서 로드했습니다.")
            return companies
        else:
            st.warning("⚠️ Supabase에서 회사 데이터를 가져올 수 없습니다. 샘플 데이터를 사용합니다.")
            return get_sample_companies()
            
    except Exception as e:
        st.error(f"회사 목록 로드 중 오류: {str(e)}")
        return get_sample_companies()

def get_sample_companies():
    """샘플 회사 목록 반환"""
    return [
        {
            'name': '블렌드액스',
            'industry': 'IT/소프트웨어',
            'region': '서울특별시',
            'business_type': '벤처기업',
            'employee_count': '11-50명',
            'business_stage': '성장기(3-7년)',
            'founding_year': 2020,
            'technology_fields': ['AI', '데이터분석'],
            'certifications': ['벤처기업확인서']
        },
        {
            'name': '테크스타트업',
            'industry': '바이오/헬스케어',
            'region': '경기도',
            'business_type': '중소기업',
            'employee_count': '6-10명',
            'business_stage': '초기창업(3년 미만)',
            'founding_year': 2022,
            'technology_fields': ['바이오', '의료기기'],
            'certifications': []
        }
    ]

def get_company_info_for_recommendation(selected_company):
    """추천 시스템에서 사용할 수 있도록 회사 정보를 변환"""
    if not selected_company:
        return None
    
    return {
        'company_name': selected_company['name'],
        'business_type': selected_company['business_type'],
        'industry': selected_company['industry'],
        'region': selected_company['region'],
        'founding_year': selected_company['founding_year'],
        'employee_count': selected_company['employee_count'],
        'business_stage': selected_company['business_stage'],
        'technology_fields': selected_company['technology_fields'],
        'certifications': selected_company['certifications']
    }

def main():
    # 메인 헤더
    st.markdown('<h1 class="main-header">🚀 스타트업 정부지원사업 추천 시스템</h1>', unsafe_allow_html=True)
    
    # 회사 목록 로드
    if 'company_list' not in st.session_state:
        st.session_state.company_list = load_company_list()
    
    # 선택된 회사 정보 (세션 상태에 저장)
    if 'selected_company' not in st.session_state:
        st.session_state.selected_company = None
        
        # 처음 실행 시 "대박드림스"를 기본으로 선택
        if st.session_state.company_list:
            default_company = next(
                (company for company in st.session_state.company_list 
                 if company['name'] == "대박드림스"), 
                None
            )
            if default_company:
                st.session_state.selected_company = default_company
    
    # 사이드바에 회사 선택 폼
    with st.sidebar:
        st.markdown("### 🏢 회사 선택")
        
        # 회사 검색 및 선택
        search_term = st.text_input("🔍 회사명 검색", placeholder="회사명을 입력하세요...")
        
        # 검색 결과 필터링
        if search_term:
            filtered_companies = [company for company in st.session_state.company_list 
                                if search_term.lower() in company['name'].lower()]
        else:
            filtered_companies = st.session_state.company_list[:20]  # 처음 20개만 표시
        
        # 회사 선택 드롭다운
        if filtered_companies:
            company_options = [f"{company['name']} ({company['industry']}, {company['region']})" 
                             for company in filtered_companies]
            
            # "대박드림스"를 기본값으로 설정
            default_index = 0
            if not search_term:  # 검색 중이 아닐 때만 기본값 적용
                for i, option in enumerate(company_options):
                    if "대박드림스" in option:
                        default_index = i + 1  # +1 because of "회사를 선택하세요..." option
                        break
            
            selected_option = st.selectbox(
                "회사 선택",
                ["회사를 선택하세요..."] + company_options,
                index=default_index
            )
            
            if selected_option != "회사를 선택하세요...":
                # 선택된 회사 정보 추출
                selected_company_name = selected_option.split(" (")[0]
                selected_company = next(
                    (company for company in filtered_companies 
                     if company['name'] == selected_company_name), 
                    None
                )
                
                if selected_company:
                    st.session_state.selected_company = selected_company
                    st.success(f"✅ {selected_company_name} 선택됨")
        else:
            st.info("검색 결과가 없습니다.")
        
        # 선택된 회사 정보 표시
        if st.session_state.selected_company:
            company = st.session_state.selected_company
            st.markdown("---")
            st.markdown("#### 📋 선택된 회사 정보")
            st.markdown(f"**회사명**: {company['name']}")
            st.markdown(f"**업종**: {company['industry']}")
            st.markdown(f"**지역**: {company['region']}")
            st.markdown(f"**사업자 유형**: {company['business_type']}")
            st.markdown(f"**직원 수**: {company['employee_count']}")
            st.markdown(f"**창업 단계**: {company['business_stage']}")
            
            # 회사 변경 버튼
            if st.button("🔄 다른 회사 선택"):
                st.session_state.selected_company = None
                st.rerun()
    
    # 메인 탭 구성
    tab1, tab2, tab3 = st.tabs(["🎯 맞춤 추천", "🔔 신규 공고 알림", "🗺️ 로드맵 생성"])
    
    with tab1:
        show_recommendation_tab()
    
    with tab2:
        show_notification_tab()
    
    with tab3:
        show_roadmap_tab()

def show_recommendation_tab():
    """맞춤 추천 탭"""
    st.markdown('<h2 class="sub-header">🎯 맞춤 추천</h2>', unsafe_allow_html=True)
    
    # Supabase 기반 추천 시스템 사용
    
    # 추천 옵션 선택
    col1, col2 = st.columns([1, 1])
    
    with col1:
        recommendation_type = st.radio(
            "추천 유형 선택",
            ["전체 공고", "활성 공고만"],
            help="활성 공고는 현재 신청 가능한 공고만을 의미합니다."
        )
    
    with col2:
        sort_option = st.selectbox(
            "정렬 기준",
            ["추천 점수 높은 순", "신청 마감일 빠른 순", "공고 등록일 최신 순"]
        )
    
    # 필터 옵션
    with st.expander("🔍 상세 필터", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_score = st.slider("최소 추천 점수", 0, 100, 0)
            support_field = st.multiselect(
                "지원분야",
                ["창업", "경영", "기술", "마케팅", "인력", "자금", "기타"],
                default=[]
            )
        
        with col2:
            target_audience = st.multiselect(
                "지원대상",
                ["창업벤처", "중소기업", "사회적기업", "일반기업", "개인", "기타"],
                default=[]
            )
            region_filter = st.multiselect(
                "지역",
                ["서울특별시", "부산광역시", "대구광역시", "인천광역시", "광주광역시", 
                 "대전광역시", "울산광역시", "세종특별자치시", "경기도", "강원도", 
                 "충청북도", "충청남도", "전라북도", "전라남도", "경상북도", "경상남도", "제주특별자치도"],
                default=[]
            )
        
        with col3:
            data_source = st.multiselect(
                "데이터 소스",
                ["bizinfo", "kstartup", "mss", "kised"],
                default=[]
            )
            max_results = st.number_input("최대 결과 수", min_value=10, max_value=500, value=50)
    
    # 추천 결과 자동 생성 및 표시
    if st.session_state.selected_company:
        with st.spinner("추천을 생성하는 중..."):
            try:
                # 선택된 회사 정보를 추천 시스템 형식으로 변환
                company_info = get_company_info_for_recommendation(st.session_state.selected_company)
                
                # 추천 실행
                recommendations = get_recommendations(
                    company_info,
                    recommendation_type,
                    min_score,
                    support_field,
                    target_audience,
                    region_filter,
                    data_source,
                    max_results
                )
                
                if recommendations is not None and not recommendations.empty:
                    st.session_state.recommendations = recommendations
                    display_recommendations(recommendations, sort_option)
                else:
                    st.warning("⚠️ 조건에 맞는 추천 공고가 없습니다. 필터 조건을 조정해보세요.")
                    
            except Exception as e:
                st.error(f"❌ 추천 생성 중 오류가 발생했습니다: {str(e)}")
    else:
        st.info("💡 먼저 사이드바에서 회사를 선택해주세요.")
        # 샘플 데이터 표시
        display_sample_recommendations()

def show_notification_tab():
    """신규 공고 알림 탭"""
    st.markdown('<h2 class="sub-header">🔔 신규 공고 알림</h2>', unsafe_allow_html=True)
    
    # 알림 현황 섹션
    st.markdown("### 📊 알림 현황")
    
    try:
        # 실제 데이터 가져오기
        all_recommendations = supabase_client.get_recommendations(is_active_only=False)
        new_announcements = supabase_client.get_recommendations(is_new_announcements=True)
        
        # 이번 주 신규 공고 수
        new_count = len(new_announcements) if new_announcements else 0
        
        # 마감 임박 공고 수 (7일 이내) 및 이번 달 공고 수
        today = datetime.now().date()
        current_month = today.month
        current_year = today.year
        urgent_count = 0
        high_score_count = 0
        this_month_count = 0
        
        if all_recommendations:
            for item in all_recommendations:
                period_str = item.get('사업 연도', '')
                if period_str:
                    # 마감일 추출
                    end_date_match = re.search(r'~\s*(\d{8})', period_str)
                    if end_date_match:
                        try:
                            end_date = datetime.strptime(end_date_match.group(1), '%Y%m%d').date()
                            days_left = (end_date - today).days
                            if 0 <= days_left <= 7:
                                urgent_count += 1
                        except ValueError:
                            pass
                    
                    # 이번 달 공고 수 계산 (시작일 기준)
                    start_date_match = re.search(r'(\d{8})\s*~', period_str)
                    if start_date_match:
                        try:
                            start_date = datetime.strptime(start_date_match.group(1), '%Y%m%d').date()
                            if start_date.month == current_month and start_date.year == current_year:
                                this_month_count += 1
                        except ValueError:
                            pass
                
                # 고점수 공고 (80점 이상)
                score = item.get('최종 점수', 0)
                if isinstance(score, (int, float)) and score >= 80:
                    high_score_count += 1
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("이번 주 신규 공고", new_count)
        
        with col2:
            st.metric("마감 임박 공고", urgent_count)
        
        with col3:
            st.metric("고점수 추천 공고", high_score_count)
        
        with col4:
            st.metric("이번 달 공고 수", this_month_count)
            
    except Exception as e:
        st.error(f"알림 현황 조회 중 오류: {str(e)}")
        # 오류 시 샘플 데이터 표시
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("이번 주 신규 공고", "23", "3")
        
        with col2:
            st.metric("마감 임박 공고", "8", "-2")
        
        with col3:
            st.metric("고점수 추천 공고", "15", "5")
        
        with col4:
            st.metric("이번 달 공고 수", "15")
    
    # 최근 신규 공고 섹션
    st.markdown("### 🆕 최근 신규 공고")
    display_new_announcements()
    
    # 마감 임박 공고 섹션
    st.markdown("### ⏰ 마감 임박 공고")
    display_deadline_announcements()

def show_roadmap_tab():
    """로드맵 생성 탭"""
    st.markdown('<h2 class="sub-header">🗺️ 로드맵 생성</h2>', unsafe_allow_html=True)
    
    # 선택된 기업이 있는지 확인
    if not st.session_state.get('selected_company'):
        st.warning("⚠️ 먼저 사이드바에서 기업을 선택해주세요.")
        return
    
    # 로드맵 표시
    display_roadmap()

def get_recommendations(startup_info, recommendation_type, min_score, support_field, 
                       target_audience, region_filter, data_source, max_results):
    """Supabase에서 추천 공고 생성"""
    try:
        # Supabase에서 추천 데이터 가져오기
        is_active_only = (recommendation_type == "활성 공고만")
        recommendations = supabase_client.get_recommendations(
            company_name=startup_info['company_name'],
            is_active_only=is_active_only
        )
        
        if not recommendations:
            st.warning(f"⚠️ '{startup_info['company_name']}'에 대한 추천 공고가 없습니다.")
            return None
        
        # DataFrame으로 변환
        df = pd.DataFrame(recommendations)
        
        # 최종 점수 기준으로 정렬
        df = df.sort_values('최종 점수', ascending=False)
        
        # 최소 점수 필터링
        if min_score > 0:
            df = df[df['최종 점수'] >= min_score]
        
        # 최대 결과 수 제한
        if max_results > 0:
            df = df.head(max_results)
        
        # 컬럼명을 기존 형식에 맞게 변경
        df = df.rename(columns={
            '사업명': '공고명',
            '최종 점수': '총점수',
            '지역': '지역명',
            '사업 연도': '신청기간',
            '상세페이지 URL': '공고URL'
        })
        
        # 순위 추가
        df['순위'] = range(1, len(df) + 1)
        
        # 데이터소스 컬럼 추가 (기본값)
        df['데이터소스'] = 'recommend_final'
        
        # 지원분야, 지원대상, 소관기관 컬럼 추가 (기본값)
        df['지원분야'] = '기타'
        df['지원대상'] = '중소기업'
        df['소관기관'] = '정부기관'
        
        st.success(f"✅ '{startup_info['company_name']}'에 대한 {len(df)}개 추천 공고를 찾았습니다!")
        
        return df
        
    except Exception as e:
        st.error(f"추천 생성 중 오류: {str(e)}")
        return None

def apply_filters(recommendations, recommendation_type, support_field, 
                 target_audience, region_filter, data_source):
    """추천 결과에 필터 적용"""
    filtered = recommendations.copy()
    
    # 활성 공고만 필터링
    if recommendation_type == "활성 공고만":
        current_date = datetime.now().date()
        filtered = filtered[
            (filtered['신청기간'].str.contains('예산 소진시까지', na=False)) |
            (filtered['신청기간'].str.contains(str(current_date.year), na=False))
        ]
    
    # 지원분야 필터
    if support_field:
        filtered = filtered[filtered['지원분야'].isin(support_field)]
    
    # 지원대상 필터
    if target_audience:
        filtered = filtered[filtered['지원대상'].isin(target_audience)]
    
    # 지역 필터
    if region_filter:
        filtered = filtered[filtered['지역명'].isin(region_filter)]
    
    # 데이터 소스 필터
    if data_source:
        filtered = filtered[filtered['데이터소스'].isin(data_source)]
    
    return filtered

def display_recommendations(recommendations, sort_option):
    """추천 결과 표시"""
    # 정렬 적용
    if sort_option == "추천 점수 높은 순":
        recommendations = recommendations.sort_values('총점수', ascending=False)
    elif sort_option == "신청 마감일 빠른 순":
        recommendations = recommendations.sort_values('신청기간', ascending=True)
    elif sort_option == "공고 등록일 최신 순":
        recommendations = recommendations.sort_values('공고명', ascending=False)
    
    # 상세 결과 테이블 (위로 이동)
    st.markdown("### 📋 상세 추천 공고")
    
    # 테이블 컬럼 선택
    display_columns = [
        '순위', '공고명', '지원분야', '지원대상', '지역명', 
        '소관기관', '신청기간', '총점수', '데이터소스'
    ]
    
    # URL 컬럼 추가 (클릭 가능한 링크로)
    if '공고URL' in recommendations.columns:
        display_columns.append('공고URL')
    
    # 테이블 표시
    display_df = recommendations[display_columns].copy()
    
    # URL을 클릭 가능한 링크로 변환
    if '공고URL' in display_df.columns:
        display_df['공고URL'] = display_df['공고URL'].apply(
            lambda x: f'<a href="{x}" target="_blank">🔗 링크</a>' if pd.notna(x) and x else ''
        )
    
    st.dataframe(
        display_df,
        width='stretch',
        hide_index=True
    )
    
    # CSV 다운로드 버튼
    csv = recommendations.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 추천 결과 CSV 다운로드",
        data=csv,
        file_name=f"recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
    
    # 추천 결과 요약 (아래로 이동)
    st.markdown("### 📊 추천 결과 요약")
    
    # 결과 요약
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 추천 수", len(recommendations))
    
    with col2:
        avg_score = recommendations['총점수'].mean()
        st.metric("평균 추천 점수", f"{avg_score:.1f}")
    
    with col3:
        high_score_count = len(recommendations[recommendations['총점수'] >= 80])
        st.metric("고점수 공고 (80점 이상)", high_score_count)
    
    with col4:
        unique_sources = recommendations['데이터소스'].nunique()
        st.metric("데이터 소스 수", unique_sources)

def display_sample_recommendations():
    """샘플 추천 데이터 표시 (데모용)"""
    st.markdown("### 📋 추천 결과 (샘플 데이터)")
    st.info("💡 실제 추천을 보려면 위의 '추천 실행' 버튼을 클릭하세요.")
    
    # 샘플 데이터
    sample_data = pd.DataFrame({
        '순위': [1, 2, 3, 4, 5],
        '공고명': [
            '2025년 서울 AI 허브 멤버십 모집 공고',
            '서울기후테크산업지원센터 경영 및 기술컨설팅 공고',
            'IP(지식재산) 디딤돌 프로그램 권리화 지원 모집 공고',
            '2025년 2차 하반기 예비사회적기업(지역형) 지정계획 공고',
            '스타트업 테크쇼'
        ],
        '지원분야': ['창업', '경영', '창업', '경영', '전시'],
        '지원대상': ['창업벤처', '중소기업', '창업벤처', '사회적기업', '중소기업'],
        '지역명': ['서울특별시', '서울특별시', '서울특별시', '서울특별시', '전국'],
        '소관기관': ['서울특별시', '서울특별시', '서울특별시', '서울특별시', 'K-스타트업'],
        '신청기간': [
            '2025.09.15 ~ 2025.10.10',
            '2025.05.09 ~ 2025.12.19',
            '예산 소진시까지',
            '2025.08.05 ~ 2025.09.30',
            '2025년'
        ],
        '총점수': [85.02, 81.82, 81.50, 75.40, 53.12],
        '데이터소스': ['bizinfo', 'bizinfo', 'bizinfo', 'bizinfo', 'kstartup_total']
    })
    
    st.dataframe(sample_data, width='stretch', hide_index=True)

def display_new_announcements():
    """Supabase에서 신규 공고 표시"""
    try:
        # Supabase에서 신규 공고 데이터 가져오기
        new_announcements = supabase_client.get_recommendations(is_new_announcements=True)
        
        if not new_announcements:
            st.info("신규 공고가 없습니다.")
            return
        
        # DataFrame으로 변환
        df = pd.DataFrame(new_announcements)
        
        # 컬럼명 변경
        df = df.rename(columns={
            '사업명': '공고명',
            '최종 점수': '추천점수',
            '지역': '지역',
            '사업 연도': '신청기간',
            '상세페이지 URL': '공고URL'
        })
        
        # 등록일 컬럼 추가 (사업 연도에서 추출)
        df['등록일'] = df['신청기간'].apply(lambda x: extract_start_date(x))
        
        # 지원분야, 지원대상, 소관기관 컬럼 추가 (기본값)
        df['지원분야'] = '기타'
        df['지원대상'] = '중소기업'
        df['소관기관'] = '정부기관'
        
        # 추천 점수에 따른 색상 코딩
        def highlight_high_score(row):
            if row['추천점수'] >= 80:
                return ['background-color: #d4edda; color: #000000'] * len(row)
            elif row['추천점수'] >= 70:
                return ['background-color: #fff3cd; color: #000000'] * len(row)
            else:
                return ['background-color: #ffffff; color: #000000'] * len(row)
        
        styled_data = df.style.apply(highlight_high_score, axis=1)
        st.dataframe(styled_data, width='stretch', hide_index=True)
        
    except Exception as e:
        st.error(f"신규 공고 조회 중 오류: {str(e)}")
        st.info("샘플 데이터를 표시합니다.")
        display_sample_new_announcements()

def extract_start_date(business_period):
    """사업 연도에서 시작 날짜 추출"""
    if not business_period:
        return datetime.now().strftime('%Y-%m-%d')
    
    import re
    date_match = re.search(r'(\d{8})', business_period)
    if date_match:
        try:
            start_date_str = date_match.group(1)
            start_date = datetime.strptime(start_date_str, '%Y%m%d')
            return start_date.strftime('%Y-%m-%d')
        except:
            return datetime.now().strftime('%Y-%m-%d')
    
    return datetime.now().strftime('%Y-%m-%d')

def display_sample_new_announcements():
    """샘플 신규 공고 표시"""
    sample_new_announcements = pd.DataFrame({
        '공고명': [
            '2025년 3기 서울 AI 허브 멤버십 모집 공고',
            '서울 스타트업 해외진출 지원사업 공고',
            '2025년 하반기 창업도약패키지 신청',
            '중소기업 기술혁신 지원사업 공고',
            '사회적기업 육성지원사업 공고',
            '벤처기업 성장지원 프로그램',
            '청년창업 지원사업 공고',
            '지역특화산업 육성사업'
        ],
        '지원분야': ['창업', '해외진출', '창업', '기술', '사회적기업', '성장', '창업', '지역특화'],
        '지원대상': ['창업벤처', '스타트업', '창업벤처', '중소기업', '사회적기업', '벤처기업', '청년', '중소기업'],
        '지역': ['서울특별시', '서울특별시', '전국', '전국', '전국', '전국', '전국', '전국'],
        '소관기관': ['서울특별시', '서울특별시', '중소벤처기업부', '중소벤처기업부', '보건복지부', '중소벤처기업부', '고용노동부', '산업통상자원부'],
        '신청기간': [
            '2025.10.01 ~ 2025.10.31',
            '2025.10.05 ~ 2025.11.15',
            '2025.10.10 ~ 2025.11.30',
            '2025.10.15 ~ 2025.12.15',
            '2025.10.20 ~ 2025.12.20',
            '2025.10.25 ~ 2025.12.25',
            '2025.11.01 ~ 2025.12.31',
            '2025.11.05 ~ 2026.01.05'
        ],
        '등록일': [
            '2025-10-01',
            '2025-10-02',
            '2025-10-03',
            '2025-10-04',
            '2025-10-05',
            '2025-10-06',
            '2025-10-07',
            '2025-10-08'
        ],
        '추천점수': [88.5, 82.3, 79.1, 76.8, 74.2, 71.9, 69.5, 67.2]
    })
    
    # 추천 점수에 따른 색상 코딩
    def highlight_high_score(row):
        if row['추천점수'] >= 80:
            return ['background-color: #d4edda; color: #000000'] * len(row)
        elif row['추천점수'] >= 70:
            return ['background-color: #fff3cd; color: #000000'] * len(row)
        else:
            return ['background-color: #ffffff; color: #000000'] * len(row)
    
    styled_data = sample_new_announcements.style.apply(highlight_high_score, axis=1)
    st.dataframe(styled_data, width='stretch', hide_index=True)

def display_deadline_announcements():
    """마감 임박 공고 표시"""
    # 샘플 마감 임박 데이터
    deadline_data = pd.DataFrame({
        '공고명': [
            '2025년 2기 서울 AI 허브 멤버십 모집 공고',
            '서울기후테크산업지원센터 경영컨설팅',
            'IP 디딤돌 프로그램 권리화 지원',
            '예비사회적기업 지정계획 공고',
            '스타트업 테크쇼 참가'
        ],
        '지원분야': ['창업', '경영', '창업', '경영', '전시'],
        '지원대상': ['창업벤처', '중소기업', '창업벤처', '사회적기업', '중소기업'],
        '지역': ['서울특별시', '서울특별시', '서울특별시', '서울특별시', '전국'],
        '마감일': ['2025-10-10', '2025-12-19', '예산 소진시까지', '2025-09-30', '2025-12-31'],
        '남은일수': [3, 45, '상시', 5, 67],
        '추천점수': [85.02, 81.82, 81.50, 75.40, 53.12]
    })
    
    # 남은 일수에 따른 색상 코딩
    def highlight_urgent(row):
        if row['남은일수'] == '상시':
            return ['background-color: #e3f2fd; color: #000000'] * len(row)
        elif isinstance(row['남은일수'], int) and row['남은일수'] <= 7:
            return ['background-color: #f8d7da; color: #000000'] * len(row)
        elif isinstance(row['남은일수'], int) and row['남은일수'] <= 14:
            return ['background-color: #fff3cd; color: #000000'] * len(row)
        else:
            return ['background-color: #ffffff; color: #000000'] * len(row)
    
    styled_data = deadline_data.style.apply(highlight_urgent, axis=1)
    st.dataframe(styled_data, width='stretch', hide_index=True)

def generate_roadmap(roadmap_type, time_horizon, priority_focus):
    """로드맵 생성"""
    st.session_state.roadmap_data = {
        'type': roadmap_type,
        'time_horizon': time_horizon,
        'priority_focus': priority_focus,
        'created_at': datetime.now()
    }
    st.success("✅ 로드맵이 생성되었습니다!")

def display_roadmap():
    """로드맵 표시 - 월별 공고 수 시각화 및 맞춤 추천 공고들"""
    st.markdown("### 🗺️ 맞춤 추천 공고 로드맵")
    
    try:
        # 선택된 기업 정보 가져오기
        selected_company = st.session_state.get('selected_company')
        if not selected_company:
            st.warning("⚠️ 먼저 사이드바에서 기업을 선택해주세요.")
            return
        
        # 월별 공고 수 시각화 먼저 표시
        
        # Supabase에서 선택된 회사의 월별 데이터 가져오기
        monthly_data = supabase_client.get_monthly_recommendations(company_name=selected_company['name'])
        
        # 월별 데이터를 DataFrame으로 변환
        months = ['1월', '2월', '3월', '4월', '5월', '6월', 
                 '7월', '8월', '9월', '10월', '11월', '12월']
        counts = [monthly_data[i] for i in range(1, 13)]
        
        monthly_df = pd.DataFrame({
            '월': months,
            '공고 수': counts
        })
        
        # 막대 그래프 생성
        fig = px.bar(
            monthly_df,
            x='월',
            y='공고 수',
            title="월별 공고 수 분포",
            color='공고 수',
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            xaxis_title="월",
            yaxis_title="공고 수",
            showlegend=False
        )
        st.plotly_chart(fig, width='stretch')
        
        # 월별 상세보기
        st.markdown("### 📋 월별 상세보기")
        
        # 월 선택 버튼들
        cols = st.columns(4)
        selected_month = None
        
        for i, month in enumerate(months):
            with cols[i % 4]:
                if st.button(f"{month} ({counts[i]}건)", key=f"month_{i+1}"):
                    selected_month = i + 1
        
        # 선택된 월의 상세 정보 표시
        if selected_month:
            st.markdown(f"### {months[selected_month-1]} 상세 공고")
            monthly_details = supabase_client.get_monthly_details(selected_month, company_name=selected_company['name'])
            
            if monthly_details:
                details_df = pd.DataFrame(monthly_details)
                st.dataframe(details_df, width='stretch', hide_index=True)
            else:
                st.info(f"{months[selected_month-1]}에는 공고가 없습니다.")
        
        
    except Exception as e:
        st.error(f"로드맵 데이터 조회 중 오류: {str(e)}")
        st.info("데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.")


if __name__ == "__main__":
    main()
