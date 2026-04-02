import os
import requests
import pytz
from datetime import datetime, timedelta
from icalendar import Calendar, Event

# --- 설정 (서울 기준) ---
NX, NY = 60, 127
REG_ID = '11B10101'      # 중기육상예보 (서울)
REG_TEMP_ID = '11B10101' # 중기기온예보 (서울)
API_KEY = os.environ.get('KMA_API_KEY')

def get_emoji(sky, pty):
    """기상청 코드 기반 이모지 변환"""
    if pty != '0':
        if pty in ['1', '4']: return "🌧️"
        if pty == '2': return "🌨️"
        if pty == '3': return "❄️"
    else:
        if sky == '1': return "☀️"
        if sky == '3': return "⛅"
        if sky == '4': return "☁️"
    return "🌡️"

def fetch_data(url):
    print(f"--- Requesting URL: {url} ---") # 호출하는 주소 확인
    res = requests.get(url)
    if res.status_code == 200:
        print("--- Response Data Start ---")
        print(res.text) # <--- 여기에 추가! 기상청이 보내준 실제 데이터 출력
        print("--- Response Data End ---")
        return res.text
    else:
        print(f"Error: Status Code {res.status_code}")
        return None

def parse_short_term():
    """단기예보 파싱: 0~3일치 데이터를 날짜별로 딕셔너리에 저장"""
    base_date = datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y%m%d')
    url = f"https://apihub.kma.go.kr/api/typ01/url/vsc_sfc_af_dtl.php?base_date={base_date}&nx={NX}&ny={NY}&authKey={API_KEY}"
    raw_data = fetch_data(url)
    
    # [노트북 파일 로직 적용 부분]
    # 기상청 API 응답 형식(#으로 시작하는 주석 제외)을 파싱하여 
    # 날짜별 TMP, SKY, PTY, POP, REH, WSD 정보를 추출하는 로직이 들어갑니다.
    # 여기서는 구조적 구현을 위해 가공된 형태를 가정합니다.
    forecasts = {} 
    # ... (데이터 파싱 로직) ...
    return forecasts

def main():
    cal = Calendar()
    cal.add('X-WR-CALNAME', '기상청 날씨 달력')
    
    # 1. 단기 예보 처리 (0~3일)
    # 2. 중기 예보 처리 (4~10일) - 중기육상/기온 API 호출 필요
    
    # 실제 기상청 API 데이터는 헤더 형식이 복잡하므로 
    # 세부 파싱을 위해 'requests' 이후 'split()' 등을 적절히 사용해야 합니다.

    # [중요] 현재는 구조가 완성되었으니, 
    # '실제 API 응답 텍스트'를 한 번 확인하고 파싱 코드를 정교화하는 단계가 필요합니다.

    with open('weather.ics', 'wb') as f:
        f.write(cal.to_ical())

if __name__ == "__main__":
    main()
