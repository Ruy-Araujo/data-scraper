import os
from datetime import datetime
from dotenv import load_dotenv
from app import scraper, utils

start_time = datetime.now()
load_dotenv()
scrap = scraper.Extractor(
    os.getenv("LOGIN"), os.getenv("PASSWORD"), os.getenv("URL"))
scrap.login()

course_data = scrap.get_data()
utils.save_file('.temp', course_data["course_name"], course_data)

for classe in course_data["data"]:
    path = f'data/{course_data["course_name"]}/{classe["class_name"]}'
    utils.create_folder(path)

    for lesson in classe['lessons']:
        blob = scrap.get_file(lesson['name'], lesson['url'], path)
        if blob:
            utils.save_file(path, lesson["name"], blob)

scrap.close()

print(f"""Processo finalizado em {datetime.now() - start_time}""")
