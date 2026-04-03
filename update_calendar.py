import os
import requests
import pytz
from datetime import datetime, timedelta
from icalendar import Calendar, Event

# --- [1. 설정] ---
# 격자 좌표 및 위치명 (원하시는 주소로 수정 가능)
NX, NY = 60, 127
LOCATION_NAME = "봉화산로 193"  # 이미지처럼 주소 표출용
REG_ID_TEMP = '11B10101'
REG_ID_LAND = '11B00000'
API_KEY = os.environ.get('KMA_API_KEY')

def get_emoji(sky, pty):
    """하늘상태(SKY)와 강수형태(PTY)를 조합해 이모지 결정"""
    sky, pty = str(sky), str(pty)
    if pty != '0':
        if pty in ['1', '4']: return "🌧️" # 비/소나기
        if pty == '2': return "🌨️"        # 비/눈
        if pty == '3': return "❄️"        # 눈
    if sky == '1': return "☀️"            # 맑음
    if sky == '3': return "⛅"            # 구름많음
    if sky == '4': return "☁️"            # 흐림
    return "🌡️"

def fetch_api(url):
    try:
        res = requests.get(url)
        if res.status_code == 200: return res.json()
    except: return None
    return None

def main():
    seoul_tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(seoul_tz)
    cal = Calendar()
    cal.add('X-WR-CALNAME', '기상청 날씨 달력')
    cal.add('X-WR-TIMEZONE', 'Asia/Seoul')

    # 단기예보 (0~3일)
    base_date = now.strftime('%Y%m%d')
    base_time = f"{max([h for h in [2, 5, 8, 11, 14, 17, 20, 23] if h <= now.hour], default=2):02d}00"
    url_short = f"https://apihub.kma.go.kr/api/typ02/openApi/VilageFcstInfoService_2.0/getVilageFcst?dataType=JSON&base_date={base_date}&base_time={base_time}&nx={NX}&ny={NY}&authKey={API_KEY}"
    
    forecast_map = {}
    short_res = fetch_api(url_short)
    if short_res and 'response' in short_res and 'body' in short_res['response']:
        items = short_res['response']['body']['items']['item']
        for it in items:
            d, t, cat, val = it['fcstDate'], it['fcstTime'], it['category'], it['fcstValue']
            if d not in forecast_map: forecast_map[d] = {}
            if t not in forecast_map[d]: forecast_map[d][t] = {}
            forecast_map[d][t][cat] = val

    # 일정 생성
    for i in range(11):
        target_dt = now + timedelta(days=i)
        d_str = target_dt.strftime('%Y%m%d')
        event = Event()
        
        if d_str in forecast_map:
            d = forecast_map[d_str]
            times = sorted(d.keys())
            tmps = [float(d[t]['TMP']) for t in times if 'TMP' in d[t]]
            t_min, t_max = int(min(tmps)), int(max(tmps))
            
            # 제목: 이모지 + 최저/최고 (예: 🌧️ 6°C / 21°C)
            mid_t = "1200" if "1200" in d else times[len(times)//2]
            rep_em = get_emoji(d[mid_t].get('SKY'), d[mid_t].get('PTY'))
            event.add('summary', f"{rep_em} {t_min}°C / {t_max}°C")
            
            # 본문 구성 (이미지 스타일)
            desc = [f"📍 {LOCATION_NAME}\n"]
            for t in times:
                it = d[t]
                em = get_emoji(it.get('SKY'), it.get('PTY'))
                # 포맷: [09h] ⛅ 15°C (☔20% 💧60% 💨2m/s)
                line = f"[{t[:2]}h] {em} {it.get('TMP')}°C (☔{it.get('POP')}% 💧{it.get('REH')}% 💨{it.get('WSD')}m/s)"
                desc.append(line)
            
            desc.append(f"\nLast update: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            event.add('description', "\n".join(desc))
        
        else: # 중기 예보 (간략 표출)
            event.add('summary', "⛅ 예보 확인")
            event.add('description', "기상청 중기예보 참조")

        event.add('dtstart', target_dt.date())
        event.add('dtend', (target_dt + timedelta(days=1)).date())
        event.add('uid', f"{d_str}@kma_weather")
        cal.add_component(event)

    with open('weather.ics', 'wb') as f:
        f.write(cal.to_ical())
    print("✅ 이미지 스타일 반영 완료!")

if __name__ == "__main__":
    main()
