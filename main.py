from itertools import groupby

import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

thread_pool = ThreadPoolExecutor(max_workers=1)
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
    url = f'https://www.kaibao1.com/api/obNativeApi/noLogin/matchesResultPB?ts={int(time.time())}&nonce={int(time.time() * 1_000_000)}'

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

    url = f"https://www.kaibao1.com/api/obNativeApi/noLogin/getMatchResultPB?ts={int(time.time())}&nonce={int(time.time() * 1_000_000)}"
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
    req = MatchResultRequest(mid=tournament['mid'], mcid=0)
    match_result = get_match_result_pb(req=req, progress=progress)
    tournament['match_result'] = match_result


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
                                              tid="107,718,37089,189,34643")

    matches_result = matches_result_pb(req=matches_result_req)
    # matches_result里面有联赛数据，如果需要请在matches_result中自行获取

    tournaments = {k: list(g) for k, g in groupby(matches_result, key=lambda x: x['tn'])}
    print("📊 当前的联赛数据为:")
    for key in tournaments.keys():
        print(f'\t🏆 {key}')
    print("🎈" + "-" * 48 + "🎈")
    print("🚀 开始获取每场比赛数据... 🚀")

    for index, key in enumerate(tournaments):
        matches = tournaments[key]
        for match in matches:
            try:
                get_match_result(match, progress=Progress(index+1, len(tournaments), match['tn']))
                time.sleep(1) # 自行控制频率
            except Exception as e:
                print(f"获取比赛数据异常:{e}")
    write_json(result_file_path, tournaments)
    print(f"✅ 获取每场比赛数据结束, 请查阅: {result_file_path} 📁")


if __name__ == '__main__':
    main()
