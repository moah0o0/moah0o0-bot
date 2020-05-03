import requests
from bs4 import BeautifulSoup
from github import Github
import json
import os


settings = {}
repo = Github(os.environ["GITHUB_ID"], os.environ["GITHUB_PW"]).get_user().get_repo(os.environ["GITHUB_REPO"])

def send(text):
	url = "https://api.telegram.org/bot{token}/sendmessage".format(token=os.environ["TOKEN"])
	params = {"text": text, "chat_id": os.environ["TELEGRAM_TARGET"], "parse_mode":'markdown'}
	r = requests.get(url, params=params)
	return r.text

def getPostList(target):
	r = BeautifulSoup(requests.get(target).text, 'html.parser')
	r = r.select("#bd_157_0 > div.bd_lst_wrp > table > tbody")[0].find_all("tr", attrs={"class":""})
	result = []
	for i in r:
		a = i.find("a")
		# data
		url = a.attrs['href']
		title = a.get_text().replace("\t", "").replace("\n","")
		time = i.find("td", attrs={"class":"time"}).get_text()
		author = i.find("td", attrs={"class":"author"}).get_text()
		view = i.find("td", attrs={"class":"m_no"}).get_text()
		# append
		data = {"url":url, "title":title, "time":time, "view":view, "author":author}
		result.append(data)
	
	return result

def remove_uploads(data, old_url):
	c = data.copy()
	for i in c:
		c[c.index(i)] = i["url"]
	return data[:c.index(old_url)]

def DB_reload():
	contents = repo.get_contents(os.environ["GITHUB_DB_NAME"])
	data = json.loads(contents.decoded_content)
	settings["last_post"] = data["last_post"]
	return data

def DB_update(last_post):
	contents = repo.get_contents(os.environ["GITHUB_DB_NAME"])
	repo.update_file(path=contents.path, message="[봇] : #last_post 값 없데이트", content=json.dumps({"last_post":last_post}), sha=contents.sha)

def main():
	a = getPostList(os.environ["INPUT"])
	DB_reload()
	if not (a[0]["url"] == settings["last_post"]):
		a = remove_uploads(a, settings["last_post"])
		print("[채널] 발송: (총 {}개)".format(len(a)))
		for i in a:
			text = os.environ["MESSAGE_FORMAT"].format(time=i["time"], url=i["url"], title=i["title"], view=i["view"], author=i['author'])
			send(text=text)
			print("[채널] 발송: 제목: {}".format(i["title"]))
		print("[채널] 발송: (완료)")
		print("[DB] 수정: (시작)")
		DB_update(last_post=a[0]["url"])
		print("[DB] 수정: (완료)")

main()
