import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re
import pandas as pd

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

class SupabaseClient:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            print("⚠️ Supabase 환경변수가 설정되지 않았습니다. Streamlit Cloud에서 환경변수를 설정해주세요.")
            self._client = None
            return
        try:
            self._client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
            print("SupabaseClient initialized.")
        except Exception as e:
            print(f"❌ Supabase 연결 실패: {e}")
            self._client = None

    def get_companies(self):
        """alpha_companies_final 테이블에서 회사 목록을 가져옵니다."""
        if not self._client:
            return []
        try:
            response = self._client.table('alpha_companies_final').select('*').execute()
            if response.data:
                # Supabase에서 가져온 데이터를 앱의 company_list 형식에 맞게 변환
                companies = []
                for item in response.data:
                    # '설립일' 컬럼이 연도만 있는 경우 처리
                    founding_year = None
                    if '설립일' in item and item['설립일']:
                        try:
                            # '설립일'이 숫자만 있는 경우 (예: 4)
                            if str(item['설립일']).isdigit():
                                founding_year = int(item['설립일'])
                            # '설립일'이 'YYYY.MM.DD.' 형식인 경우 (예: 2020.01.01.)
                            elif re.match(r'^\d{4}\.\d{2}\.\d{2}\.$', item['설립일']):
                                founding_year = int(item['설립일'].split('.')[0])
                            # '설립일'이 'YYYY' 형식인 경우
                            elif re.match(r'^\d{4}$', item['설립일']):
                                founding_year = int(item['설립일'])
                        except ValueError:
                            pass # 변환 실패 시 None 유지

                    # '고용' 컬럼 처리 (예: '6명' -> '6-10명' 범위로 매핑)
                    employee_count_str = item.get('고용', '0명').replace('명', '').strip()
                    employee_count = '0명'
                    if employee_count_str.isdigit():
                        count = int(employee_count_str)
                        if count <= 5:
                            employee_count = '1-5명'
                        elif count <= 10:
                            employee_count = '6-10명'
                        elif count <= 50:
                            employee_count = '11-50명'
                        elif count <= 100:
                            employee_count = '51-100명'
                        elif count <= 300:
                            employee_count = '101-300명'
                        else:
                            employee_count = '300명 이상'
                    
                    # '업력' 컬럼을 'business_stage'로 매핑
                    business_stage = '예비창업자'
                    if '업력' in item and item['업력']:
                        if '3년 미만' in item['업력'] or '초기' in item['업력']:
                            business_stage = '초기창업(3년 미만)'
                        elif '3-7년' in item['업력'] or '성장' in item['업력']:
                            business_stage = '성장기(3-7년)'
                        elif '7년 이상' in item['업력'] or '성숙' in item['업력']:
                            business_stage = '성숙기(7년 이상)'
                        elif '예비' in item['업력']:
                            business_stage = '예비창업자'
                    
                    # '기술특허'와 '기업인증'을 리스트로 변환
                    technology_fields = [f.strip() for f in item.get('기술특허', '').split(',') if f.strip()]
                    certifications = [c.strip() for c in item.get('기업인증', '').split(',') if c.strip()]

                    companies.append({
                        'name': item.get('기업명', '알 수 없음'),
                        'business_type': item.get('기업형태', '법인사업자'),
                        'industry': item.get('업종', '기타'),
                        'region': item.get('지역', '전국'),
                        'founding_year': founding_year,
                        'employee_count': employee_count,
                        'business_stage': business_stage,
                        'technology_fields': technology_fields,
                        'certifications': certifications
                    })
                return companies
            return []
        except Exception as e:
            print(f"Error fetching companies from Supabase: {e}")
            return []

    def get_recommendations(self, company_name: str, is_active_only: bool = False, is_new_announcements: bool = False):
        """recommend_final 테이블에서 추천 공고를 가져옵니다."""
        if not self._client:
            return []
        try:
            query = self._client.table('recommend_final').select('*').eq('기업명', company_name)

            if is_active_only or is_new_announcements:
                today = datetime.now().date()
                # '사업 연도' 컬럼에서 시작일과 종료일 파싱
                response = query.execute()
                filtered_data = []
                for item in response.data:
                    period_str = item.get('사업 연도')
                    if not period_str:
                        continue

                    start_date_match = re.search(r'(\d{8})\s*~', period_str)
                    end_date_match = re.search(r'~\s*(\d{8})', period_str)

                    start_date = None
                    end_date = None

                    if start_date_match:
                        try:
                            start_date = datetime.strptime(start_date_match.group(1), '%Y%m%d').date()
                        except ValueError:
                            pass
                    if end_date_match:
                        try:
                            end_date = datetime.strptime(end_date_match.group(1), '%Y%m%d').date()
                        except ValueError:
                            pass
                    
                    # '예산 소진시까지' 또는 '상시' 처리
                    if '예산 소진시까지' in period_str or '상시' in period_str:
                        is_always_active = True
                    else:
                        is_always_active = False

                    if is_active_only:
                        if is_always_active or (start_date and end_date and start_date <= today <= end_date):
                            filtered_data.append(item)
                    elif is_new_announcements:
                        if start_date and (today - start_date).days <= 5: # 5일 이내 신규 공고
                            filtered_data.append(item)
                    else: # 전체 공고
                        filtered_data.append(item)
                return filtered_data
            
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Error fetching recommendations from Supabase: {e}")
            return []

    def get_monthly_recommendations(self, company_name: str = None):
        """월별 공고 수를 가져옵니다. 회사명이 지정되면 해당 회사의 추천 공고만 대상으로 합니다."""
        if not self._client:
            return {i: 0 for i in range(1, 13)}
        try:
            if company_name:
                # 특정 회사의 추천 공고만 가져오기 (전체 데이터 가져온 후 필터링)
                response = self._client.table('recommend_final').select('*').eq('기업명', company_name).execute()
            else:
                # 모든 공고 가져오기 (전체 데이터 가져온 후 필터링)
                response = self._client.table('recommend_final').select('*').execute()
            
            monthly_counts = {i: 0 for i in range(1, 13)}
            
            for item in response.data:
                period_str = item.get('사업 연도', '')
                if not period_str:
                    continue
                
                # 더 포괄적인 날짜 패턴 시도
                date_patterns = [
                    r'"(\d{8})"',  # "yyyymmdd" 형식
                    r'(\d{8})\s*~',  # yyyymmdd ~ 형식  
                    r'(\d{8})',  # 일반 yyyymmdd 형식
                    r'(\d{4})년\s*(\d{1,2})월',  # 2025년 1월 형식
                    r'(\d{4})\.(\d{1,2})\.(\d{1,2})',  # 2025.01.15 형식
                ]
                
                parsed = False
                for pattern in date_patterns:
                    match = re.search(pattern, period_str)
                    if match:
                        try:
                            if pattern == r'(\d{4})년\s*(\d{1,2})월':
                                # 2025년 1월 형식
                                year = int(match.group(1))
                                month = int(match.group(2))
                                monthly_counts[month] += 1
                                parsed = True
                                break
                            elif pattern == r'(\d{4})\.(\d{1,2})\.(\d{1,2})':
                                # 2025.01.15 형식
                                year = int(match.group(1))
                                month = int(match.group(2))
                                monthly_counts[month] += 1
                                parsed = True
                                break
                            else:
                                # yyyymmdd 형식
                                start_date_str = match.group(1)
                                start_date = datetime.strptime(start_date_str, '%Y%m%d').date()
                                month = start_date.month
                                monthly_counts[month] += 1
                                parsed = True
                                break
                        except:
                            continue
                
                # 연도만 있는 경우 (예: "2025")는 제외 - yyyymmdd ~ yyyymmdd 형식만 사용
                # if not parsed and period_str.isdigit() and len(period_str) == 4:
                #     # 연도만 있는 데이터는 제외
                #     pass
            
            return monthly_counts
        except Exception as e:
            print(f"Error fetching monthly recommendations from Supabase: {e}")
            return {i: 0 for i in range(1, 13)}

    def get_monthly_details(self, month: int, company_name: str = None):
        """특정 월의 상세 공고 목록을 가져옵니다. 회사명이 지정되면 해당 회사의 추천 공고만 대상으로 합니다."""
        if not self._client:
            return []
        try:
            if company_name:
                # 특정 회사의 추천 공고만 가져오기
                response = self._client.table('recommend_final').select('*').eq('기업명', company_name).execute()
            else:
                # 모든 공고 가져오기
                response = self._client.table('recommend_final').select('*').execute()
            
            monthly_details = []
            for item in response.data:
                period_str = item.get('사업 연도', '')
                if not period_str:
                    continue
                
                # 더 포괄적인 날짜 패턴 시도
                date_patterns = [
                    r'"(\d{8})"',  # "yyyymmdd" 형식
                    r'(\d{8})\s*~',  # yyyymmdd ~ 형식  
                    r'(\d{8})',  # 일반 yyyymmdd 형식
                    r'(\d{4})년\s*(\d{1,2})월',  # 2025년 1월 형식
                    r'(\d{4})\.(\d{1,2})\.(\d{1,2})',  # 2025.01.15 형식
                ]
                
                parsed = False
                for pattern in date_patterns:
                    match = re.search(pattern, period_str)
                    if match:
                        try:
                            if pattern == r'(\d{4})년\s*(\d{1,2})월':
                                # 2025년 1월 형식
                                year = int(match.group(1))
                                item_month = int(match.group(2))
                                if item_month == month:
                                    monthly_details.append(item)
                                parsed = True
                                break
                            elif pattern == r'(\d{4})\.(\d{1,2})\.(\d{1,2})':
                                # 2025.01.15 형식
                                year = int(match.group(1))
                                item_month = int(match.group(2))
                                if item_month == month:
                                    monthly_details.append(item)
                                parsed = True
                                break
                            else:
                                # yyyymmdd 형식
                                start_date_str = match.group(1)
                                start_date = datetime.strptime(start_date_str, '%Y%m%d').date()
                                if start_date.month == month:
                                    monthly_details.append(item)
                                parsed = True
                                break
                        except:
                            continue
                
                # 연도만 있는 경우 (예: "2025")는 제외 - yyyymmdd ~ yyyymmdd 형식만 사용
                # if not parsed and period_str.isdigit() and len(period_str) == 4:
                #     # 연도만 있는 데이터는 제외
                #     pass
            
            # 컬럼명 변경
            df = pd.DataFrame(monthly_details)
            if not df.empty:
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
                return df.to_dict('records')
            return []
        except Exception as e:
            print(f"Error fetching monthly details from Supabase: {e}")
            return []

supabase_client = SupabaseClient()
