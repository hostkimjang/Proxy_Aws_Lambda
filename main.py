import pprint
import requests
import time
from httpx import AsyncClient, AsyncHTTPTransport
import asyncio
import gzip
import base64
from quart import Quart, jsonify, request
from mangum import Mangum

app = Quart(__name__)

headers = {
    "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
}

start_time = time.time()
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    return handler(event, context)

async def fetch_data(url, identifier):
    async with AsyncClient(transport=AsyncHTTPTransport(verify=False, retries=5)) as client:
        response = await client.get(url=url, headers=headers, follow_redirects=True, timeout=30)
        pprint.pprint(response)
        compressed_data = gzip.compress(response.text.encode('utf-8'), compresslevel=6)
        compressed_data_base64 = base64.b64encode(compressed_data).decode('utf-8')

        return ({
            'identifier': identifier,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content': compressed_data_base64,
            'url': url
        })

@app.route('/')
async def index():
    return jsonify(status=200, message=f"Hello world~!")

@app.route('/mulrequest')
async def test():
    total = []
    url_params = request.args.to_dict()
    if not url_params:
        return jsonify(status=200, message=f"test world!")
    else:
        url_param = request.args.to_dict()
        param_values = list(url_param.values())
        sort_param = sorted(param_values)
        ip = f"http://ip-api.com/json"
        connect_ip = requests.get(url=ip, headers=headers)
        ip_info = connect_ip.json()
        print(sort_param)
        tasks = []
        for index, url_param in enumerate(param_values):  # 고유한 식별자를 인덱스로 사용
            url = f"https://{url_param}"
            task = asyncio.create_task(fetch_data(url, index))
            tasks.append(task)

        # 비동기 작업을 병렬로 실행하고 결과를 기다립니다.
        results = await asyncio.gather(*tasks)

        # 결과를 고유한 식별자를 기준으로 정렬합니다.
        sorted_results = sorted(results, key=lambda x: x['identifier'])

        # 결과를 total 리스트에 추가합니다.
        total.extend(sorted_results)  # 또는 total += results

        return jsonify({
            'statusCode': 200,
            'encode_info': 'gzip -> base64',
            'body': {
                "connect_ip": ip_info,
                "Response": sorted_results
            }
        })

@app.route('/request')
async def req():
    if not request.args.to_dict():
        return jsonify(status=200, message='OK')
    else:
        url_param = request.args.to_dict()
        param_values = list(url_param.values())
        result = '/'.join(map(str, param_values))

        url = f"https://{result}"
        ip = f"http://ip-api.com/json"
        connect_ip = requests.get(url=ip, headers=headers)
        ip_info = connect_ip.json()
        res = requests.get(url=url, headers=headers)
        data = {
            'status_code': res.status_code,
            'headers': dict(res.headers),
            'content': res.text
        }

        return jsonify({
            'statusCode': 200,
            'body': {
                "connect_ip": ip_info,
                "Response": data
            }
        })

@app.route('/time')
def run_time():
    end_time = time.time()
    execution_time_seconds = end_time - start_time
    return jsonify(status=200, message=f'Server is running since {execution_time_seconds}초')

# local test
if __name__ == '__main__':
    start_time = time.time()
    app.run(debug=True)

