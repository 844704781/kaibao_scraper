from itertools import groupby

import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

thread_pool = ThreadPoolExecutor(max_workers=3)
result_file_path = 'result.json'

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN,zh;q=0.9',
    'content-type': 'application/json',
    'origin': 'https://www.kaibao1.com',
    'priority': 'u=1, i',
    'referer': 'https://www.kaibao1.com/',
    'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    'x-auth-token': '',
    'x-terminal-type': 'pc',
}


# 联赛列表请求数据
class MatchesResultRequest:
    def __init__(self, euid: str, search_date: str, sort: int, _type: int, device: str, tid: str):
        self.euid = euid
        self.searchDate = search_date
        self.sort = sort
        self.type = _type
        self.device = device
        self.tid = tid


# 单场比赛结果请求数据
class MatchResultRequest:
    def __init__(self, mid: str, mcid: int):
        self.mid = mid
        self.mcid = mcid


# 进度
class Progress:
    def __init__(self, _index: int, _sum: int, tournament_name: str):
        self.index = _index
        self.sum = _sum
        self.tn = tournament_name


# 获取某一天的数据
def matches_result_pb(req: MatchesResultRequest):
    url = f'https://www.kaibao1.com/api/obNativeApi/noLogin/matchesResultPB?ts={int(time.time())}&nonce={time.time_ns()}'

    response = requests.post(url, headers=headers, json=req.__dict__)
    if not response.ok:
        print(f"😢 数据获取失败，返回: {response.text}")
        return

    resp = response.json()
    if resp.get('data') is None:
        print(f"⚠️ 获取联赛数据出错, 原因：{response.text}")
        return
    return resp['data']


# 获取某一场比赛的结果
def get_match_result_pb(req: MatchResultRequest, progress: Progress):
    mid = req.mid
    print(f"🎉 进度: {progress.index}/{progress.sum}, 当前联赛: {progress.tn}, 开始收集比赛ID: {mid} 数据")

    url = f"https://www.kaibao1.com/api/obNativeApi/noLogin/getMatchResultPB?ts={int(time.time())}&nonce={time.time_ns()}"
    response = requests.post(url, headers=headers, json=req.__dict__)
    if not response.ok:
        print(f"⚠️ 获取比赛数据出错, 原因：{response.text}")
        return
    resp = response.json()
    if resp.get('data') is None:
        print(f"⚠️ 获取比赛数据出错, 原因：{response.text}")
        return
    return resp['data']


def get_match_result(tournament: dict, progress: Progress):
    try:
        req = MatchResultRequest(mid=tournament['mid'], mcid=0)
        match_result = get_match_result_pb(req=req, progress=progress)
        tournament['match_result'] = match_result
    except Exception as e:
        print(f"获取比赛数据异常:{e}")


def write_json(file_name, data):
    with open(file_name, "w", encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def main():
    # search_date更换为你要筛选的日期
    # tid更换为你要筛选的联赛ID
    print("🎈" + "-" * 48 + "🎈")
    print("✨ 开始获取联赛数据... ✨")
    print("📝 tips: 修改代码中的search_date和tid即可更换要爬取的日期和联赛ID")
    matches_result_req = MatchesResultRequest(euid="1",
                                              search_date="2024-10-18",
                                              sort=2,
                                              _type=28,
                                              device="v2_h5_st",
                                              tid=
                                              "230,166,20312,20314,34643,35787,37777,182,217,918,20122,20123,20124,513,18039,31172,31208,37045,37089,273,1680,10782,33586,33587,343264595247255555,352541568130764801,1682748461414224369,1682748478869187623,675,2439,706,3984,3800,24447,37171,37889,2078,681,80,3663,12685,31984,2606,10162,3376,10183,22535,13912,311,7739,756,414,592,1689,23938,24324,31631,37706,401,412,454,460,462,475,480,527,570,24712,24713,26103,403,484,1225,1655,2100,17502,19912,24870,25879,25992,28452,37943,400,458,496,529,11278,31774,32,2036,3917,5024,13130,24826,26602,26693,29112,37559,581,33623,1212,1832,2580,3382,3715,21060,30886,4958,12380,13115,20460,25709,29693,37463,37717,2908,539,3091,1533,2314"
                                              )

    matches_result = matches_result_pb(req=matches_result_req)
    # matches_result里面有联赛数据，如果需要请在matches_result中自行获取

    tournaments = {k: list(g) for k, g in groupby(matches_result, key=lambda x: x['tn'])}
    print("📊 当前的联赛数据为:")
    for key in tournaments.keys():
        print(f'\t🏆 {key}')
    print("🎈" + "-" * 48 + "🎈")
    print("🚀 开始获取每场比赛数据... 🚀")
    # 同步获取(如果不想多线程获取，可以试下这个)
    # for index, key in enumerate(tournaments):
    #     matches = tournaments[key]
    #     for match in matches:
    #         get_match_result(match, progress=Progress(index + 1, len(tournaments), match['tn']))
    #         # time.sleep(1)  # 自行控制频率
    futures = []
    for index, key in enumerate(tournaments):
        matches = tournaments[key]
        for match in matches:
            futures.append(thread_pool.submit(get_match_result, match, Progress(_index=index+1, _sum=len(tournaments),
                                                                                tournament_name=match['tn'])))
    for future in as_completed(futures):
        future.result()
    write_json(result_file_path, tournaments)
    print(f"✅ 获取每场比赛数据结束, 请查阅: {result_file_path} 📁")


if __name__ == '__main__':
    main()
