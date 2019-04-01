import requests
from bs4 import BeautifulSoup
from codecs import open
import json
import csv
from configparser import ConfigParser
import os
import sys
import smtplib
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase


# Find config path
base_path = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(base_path, "config.ini")

# Check correct path
if os.path.exists(config_path):
    cfg = ConfigParser()
    cfg.read(config_path)
else:
    print("Config( %s ) not found! Exiting!" % config_path)
    sys.exit(1)


site_url = 'https://www.avito.ru/ekaterinburg/vakansii/bez_opyta_studenty'
result = []
filter_result = []
FROM = cfg.get('email', 'FROM')
TO = cfg.get('messege', 'TO')
PASSWORD = cfg.get('email', 'PASSWORD')
SUBJECT = cfg.get('messege', 'SUBJECT')
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 5.1; rv:47.0) Gecko/20100101 Firefox/47.0',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}


def soup(url):
	session = requests.Session()
	request = session.get(url, headers=headers)

	if request.status_code == 200:

		soup = BeautifulSoup(request.content, 'lxml')

		if soup != None:
			print(f'Успешное соединение с {url}')
		return soup
	else:
		print(f'Ошибка подключения.\n Код состояния: {request.status_code}')
		exit()


# get count of pages
def get_pages(soup):
	last_page_list = soup.findAll('a', class_='pagination-page')
	for item in last_page_list:
		if item.string == 'Последняя':
			last_page = item
			pages = int(last_page.get('href')[-1])
			break
	print(f'Количество страниц: {pages}')
	return pages



#get info on each page
def pars(site_url, pages):
	for page in range(pages):
		site_url = f'{site_url}?p={page+1}'
		page_response = requests.get(site_url)
		page_content = page_response.content

		soup = BeautifulSoup(page_content, 'lxml')

		info = soup.findAll('div', class_='description item_table-description')

		for i in info:
			title = i.contents[1].contents[1].contents[1].contents[1].string
			prise = i.contents[1].contents[3].contents[2].get('content')
			result.append({'title': title,'prise': prise})

	if result != None:
		print(f'Успешно спаршено {len(result)} данных')



def filter():
	for i in result:
		if int(i.get('prise')) > 20000:
			filter_result.append(i)
	print(f'Данные успешно профильтрованы. Осталось {len(filter_result)} ')


def create_json():
	with open('data.json', 'w', 'utf-8') as file:
		json.dump(filter_result, file, ensure_ascii=False)
	print('Создан файл data.json! ')



def create_csv():
	with open('data.csv', 'w',encoding='cp1251') as file:
		csvwriter = csv.writer(file, delimiter=',')
		count = 0

		for i in filter_result:

			if count == 0:
					header = i.keys()
					csvwriter.writerow(header)
					count += 1

			csvwriter.writerow(i.values())
	print('Cоздан файл data.csv!')			

def send_email():
	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.ehlo()
	server.starttls()
	server.login(FROM, PASSWORD)

	msg = MIMEMultipart("alternative")
	msg["Subject"] = SUBJECT
	msg["From"] = FROM
	msg["To"] = TO

	filename = 'data.csv'

	with open(filename, 'rb') as file:
		part2 = MIMEBase("application", "octet-stream")
		part2.set_payload(file.read())

	encoders.encode_base64(part2)
	part2.add_header(
		"Content-Disposition",
		f"attachment; filename= {filename}",
	)

	html = f'''
	<!DOCTYPE html>
	<html lang="en">
		<head>
			<meta charset="UTF-8">
			<title>Document</title>
		</head>
		<body>
			<h3>Привет, я парсер</h3>
			<p>Это полученные данные с сайта {site_url}</p>
		</body>
	</html>
	'''
	
	part = MIMEText(html, "html")
	msg.attach(part2)
	msg.attach(part)

	try:
		server.sendmail('kostya.nik.3854@gmail.com', ['kostya.nik.3854@gmail.com'], msg.as_string())
		print(f'Сообщение на адрес {TO} успешно отправлено!')
	except:
		print('Не удалось отправить сообщение!')
		server.quit()


def main():

	pars(site_url, get_pages(soup(site_url)))
	filter()

	if cfg.get('do', 'json') == '1':
		create_json()
	
	if cfg.get('do', 'csv') == '1':
		create_csv()
	if cfg.get('do', 'email') == '1':
		send_email()

main()