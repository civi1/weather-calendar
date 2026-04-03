import os
import requests
import pytz
from datetime import datetime, timedelta
from icalendar import Calendar, Event

NX, NY = 60, 127
REG_ID_TEMP = '11B10101'
REG_ID_LAND = '11B00000'
API_KEY = os.environ.get('KMA_API_KEY')

def get_emoji(wf_or_sky, pty='0'):
    wf = str(wf_or_sky)
    if '비' in wf or '소나기' in wf: return "🌧️"
    if '눈' in wf: return "🌨️"
    if '구름많음' in wf: return "⛅"
    if '흐림' in wf: return "☁️"
    if '맑음' in wf or wf == '1': return "☀️"
    if pty != '0': return "🌧️"
    return "☀️"

def main():
    seoul_tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(seoul_tz)
    cal = Calendar()
    cal.add('prodid', '-//KMA Weather Calendar//mxm.dk//')
    cal.add('version', '2.0')
    cal.add('X-WR-CALNAME', '기상청 날씨')
    cal.add('X-WR-TIMEZONE', 'Asia/Seoul')

    # 단기예보 데이터 가져오기
    base_date = now.strftime('%Y%m%d')
    base_time = f"{max([h for h in [2, 5, 8, 11, 14, 17, 20, 23] if h <= now.hour], default=2):02d}00"
    url = f"https://apihub.kma.go.kr/api/typ02/openApi/VilageFcstInfoService_2.0/getVilageFcst?dataType=JSON&base_date={base_date}&base_time={base_time}&nx={NX}&ny={NY}&authKey={API_KEY}"
    
    try:
        res = requests.get(url).json()
        items = res['response']['body']['items']['item']
        forecast = {}
        for it in items:
            d, t, c, v = it['fcstDate'], it['fcstTime'], it['category'], it['fcstValue']
            if d not in forecast: forecast[d] = {}
            if t not in forecast[d]: forecast[d][t] = {}
            forecast[d][t][c] = v

        for i in range(11):
            target = now + timedelta(days=i)
            d_str = target.strftime('%Y%m%d')
            event = Event()
            
            if d_str in forecast:
                d_data = forecast[d_str]
                times = sorted(d_data.keys())
                tmps = [float(d_data[t]['TMP']) for t in times if 'TMP' in d_data[t]]
                t_min, t_max = int(min(tmps)), int(max(tmps))
                mid_t = "1200" if "1200" in d_data else times[len(times)//2]
                emoji = get_emoji(d_data[mid_t].get('SKY'), d_data[mid_t].get('PTY'))
                
                event.add('summary', f"{emoji} {t_min}°/{t_max}°")
                desc = "\n".join([f"{t[:2]}시: {get_emoji(d_data[t].get('SKY'), d_data[t].get('PTY'))} {d_data[t].get('TMP')}°" for t in times])
                event.add('description', desc)
            else:
                event.add('summary', "⛅ 예보 확인")
                event.add('description', "중기 예보 참조")

            event.add('dtstart', target.date())
            event.add('dtend', (target + timedelta(days=1)).date())
            event.add('dtstamp', datetime.now())
            # 고유 ID 추가 (구글 캘린더 중복 방지)
            event.add('uid', f"{d_str}@kma_weather")
            cal.add_component(event)

        with open('weather.ics', 'wb') as f:
            f.write(cal.to_ical())
        print("✅ 캘린더 최적화 완료")
    except:
        print("❌ 실패")

if __name__ == "__main__":
    main()
