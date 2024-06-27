import time
import requests
import csv
from datetime import datetime, timedelta

url = "https://api.github.com/search/repositories"
params_base = {
    'q': 'language:python classification',
    'per_page': 100,
    'sort': 'stars',
    'order': 'desc',
}

headers = {
    'User-Agent': 'Mozilla/5.0',
    'Authorization': 'token YOURTOKEN',  # Replace with a valid token
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

all_data = []
csv_filename = 'YOURPATH.csv'

def append_to_csv(time):
    with open(csv_filename, 'a', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['order', 'name', 'clone_url', 'stars', 'description', 'topics', 'created_at', 'updated_at']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        if csv_file.tell() == 0:
            writer.writeheader()

        writer.writerows(all_data)
    all_data.clear()
    print(f'{time} appended to {csv_filename}')

start_date = datetime.strptime('2012-04-01', '%Y-%m-%d')
stop_date = datetime.strptime('2024-04-01', '%Y-%m-%d')
loop_cnt = 1
order_global = 1

def get_total_count(start_date, end_date):
    params = params_base.copy()
    params['q'] += f' created:{start_date.strftime("%Y-%m-%d")}..{end_date.strftime("%Y-%m-%d")}'
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    return data.get('total_count', 0)

if __name__ == '__main__':
    while start_date < stop_date:
        # Using binary search to find a time interval close to 1000 results
        if start_date < datetime.strptime('2018-04-25', '%Y-%m-%d'):
            day_intervals = [1000, 500, 200, 50, 25, 12, 6, 3, 1]
        else:
            day_intervals = [50, 25, 12, 6, 3, 1]

        for days in day_intervals:
            end_date = start_date + timedelta(days=days)
            if end_date > stop_date:
                end_date = stop_date
            total_count = get_total_count(start_date, end_date)
            print('Interval:', days, 'Total Count:', total_count)
            if total_count < 1000:
                break

        params = params_base.copy()
        params['q'] += f' created:{start_date.strftime("%Y-%m-%d")}..{end_date.strftime("%Y-%m-%d")}'

        page = 1
        while True:
            params['page'] = page
            response = requests.get(url, params=params, headers=headers)
            data = response.json()
            if response.status_code == 200:
                repositories = data.get('items', [])

                if not repositories:
                    break

                for repo in repositories:
                    name = repo.get('full_name', 'None')
                    clone_url = repo.get('clone_url', 'None')
                    stars = repo.get('stargazers_count', 'None')
                    topics = repo.get('topics', 'None')
                    description = repo.get('description', 'None')
                    created_at = repo.get('created_at', 'None')
                    updated_at = repo.get('updated_at', 'None')  # Might not be accurate

                    all_data.append({
                        'order': order_global,
                        'name': name,
                        'clone_url': clone_url,
                        'stars': stars,
                        'description': description,
                        'topics': topics,
                        'created_at': created_at,
                        'updated_at': updated_at,
                    })
                    order_global += 1

                if 'Link' in response.headers and 'rel="next"' in response.headers['Link']:
                    page += 1
                else:
                    break
            else:
                print(f'Error: {response.status_code}')
                print(data)
                break

        start_date = end_date + timedelta(days=1)

        if start_date > stop_date:  # Last batch if end_date == stop_date
            break

        print(f"{end_date} current repos: {len(all_data)}")
        if loop_cnt % 2 == 0:
            append_to_csv(end_date)
        loop_cnt += 1
        time.sleep(4)

    append_to_csv(end_date)
    print(f'Data extracted and saved to {csv_filename}')
