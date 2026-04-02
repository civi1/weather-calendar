import os
import requests
import pytz
from datetime import datetime, timedelta
from icalendar import Calendar, Event

# --- 설정 ---
NX, NY = 60, 127
REG_ID = '11B10101'
API_KEY = os.environ.get('KMA_API_KEY')

def get_weather_emoji(wf_or_sky, pty='0'):
    """단기/중기 통합 이모지 변환"""
    # 중기예보 텍스트 기반
    if any(x in wf_or_sky for x in ['비', '소나기']): return "🌧️"
    if '눈' in wf_or_sky: return "🌨️"
    if '구름많음' in wf_or_sky: return "⛅"
    if '흐림' in wf_or_sky: return "☁️"
    if '맑음' in wf_or_sky: return "☀️"
    # 단기예보 코드 기반 (숫자 들어올 경우)
    if pty != '0': return "🌧️"
    if wf_or_sky == '1': return "☀️"
    if wf_or_sky == '3': return "⛅"
    if wf_or_sky == '4': return "☁️"
    return "🌡️"

def fetch_kma(url):
    try:
        res = requests.get(url)
        if res.status_code == 200:
            if "인증실패" in res.text or "SERVICE_KEY_IS_NOT_REGISTERED_ERROR" in res.text:
                print(f"❌ API 인증 실패: {url.split('authKey=')[0]}")
                return None
            return res.text
    except Exception as e:
        print(f"❌ 네트워크 에러: {e}")
    return None

def main():
    seoul_tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(seoul_tz)
    cal = Calendar()
    cal.add('X-WR-CALNAME', '기상청 날씨 달력')

    # 1. 단기 예보 (0~3일)
    base_date = now.strftime('%Y%m%d')
    short_url = f"https://apihub.kma.go.kr/api/typ01/url/vsc_sfc_af_dtl.php?base_date={base_date}&nx={NX}&ny={NY}&authKey={API_KEY}"
    raw_short = fetch_kma(short_url)
    
    forecast_map = {} # { '20231027': { 'temps': [], 'desc': [] } }

    if raw_short:
        lines = [l for l in raw_short.split('\n') if not l.startswith('#') and len(l.split()) > 10]
        for line in lines:
            cols = line.split()
            date, hour = cols[0], cols[1]
            temp, sky, pty, pop, reh, wsd = cols[12], cols[13], cols[14], cols[15], cols[16], cols[17]
            
            if date not in forecast_map:
                forecast_map[date] = {'temps': [], 'details': []}
            
            forecast_map[date]['temps'].append(float(temp))
            emoji = get_weather_emoji(sky, pty)
            forecast_map[date]['details'].append(f"[{hour[:2]}:00] {emoji} {temp}°C, ☔{pop}%, 💧{reh}%, 💨{wsd}m/s")

    # 2. 캘린더 이벤트 생성 (오늘부터 10일치)
    for i in range(11):
        target_dt = now + timedelta(days=i)
        date_str = target_dt.strftime('%Y%m%d')
        event = Event()
        
        if date_str in forecast_map:
            # 단기 데이터가 있는 경우
            data = forecast_map[date_str]
            t_min, t_max = min(data['temps']), max(data['temps'])
            # 낮 12시 혹은 중간 시간대 날씨를 대표로 설정
            rep_idx = len(data['details']) // 2
            rep_emoji = data['details'][rep_idx].split()[1]
            
            event.add('summary', f"{rep_emoji} {t_min}° / {t_max}°")
            event.add('description', "\n".join(data['details']))
        else:
            # 데이터가 없는 날(중기 구간 등)은 기본값만 생성
            event.add('summary', "날씨 정보 업데이트 대기 중")
            event.add('description', "기상청 중기예보 데이터를 불러오는 중입니다.")

        event.add('dtstart', target_dt.date())
        event.add('dtend', target_dt.date() + timedelta(days=1))
        cal.add_component(event)

    with open('weather.ics', 'wb') as f:
        f.write(cal.to_ical())
    print(f"✅ 생성 완료: {datetime.now()}")

if __name__ == "__main__":
    main()
