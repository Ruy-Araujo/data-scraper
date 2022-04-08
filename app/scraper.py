import os
import requests
import urllib.parse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions as EC

import m3u8


class Extractor():

    def __init__(self, username, password, url):

        self.username = username
        self.password = password
        self.url = url

        # Chrome Driver
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        # chrome_options.add_argument("--headless")  # não criar janela do chrome
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # desabilitar logs do chrome driver
        chrome_options.add_argument("--log-level=3")
        try:
            print(f"{os.getcwd()}/driver/chromedriver")
            self.driver = webdriver.Chrome(
                executable_path=f"{os.getcwd()}/driver/chromedriver", options=chrome_options, service_log_path=None)
            self.session = requests.Session()
        except WebDriverException:
            print("""Erro não foi possivel carregar o webdriver verifique a pasta 'driver' ou siga 
                  https://www.selenium.dev/pt-br/documentation/webdriver/getting_started/install_drivers/""")

    def __wait_load(self, query="", time=20000000000):
        """Wait until finder loads in page to continue

        Args:
            finder_query (string): Query to locate element (use single quote)
            time(int): Time to wait.
        """
        WebDriverWait(self.driver, timeout=time).until(
            EC.presence_of_element_located((By.XPATH, f'{query}')))

    def __find(self, query=""):
        return self.driver.find_element(
            By.XPATH, f'{query}')

    def __find_all(self, query=""):
        return self.driver.find_elements(
            By.XPATH, f'{query}')

    def __download_pdf(self, url):
        response = self.session.get(url)
        return response.content

    def __download_m3u8(self, url, lesson_name, path):
        if not "https://" in url or not "http://" in url:
            url = "http:" + url
        playlist = m3u8.load(url)
        index_m3u8 = playlist.playlists[-1].base_uri + \
            playlist.playlists[-1].uri
        os.system(
            f'downloadm3u8 -o "{path}/{lesson_name}".mp4 {index_m3u8}')
        return

    def __download_zip(self, url):
        response = self.session.get(url, stream=True)
        return response

    def login(self):
        self.driver.get(self.url)

        self.__wait_load('//button[@type="submit"]')

        username_input = self.__find('//*[@id="deslogin"]')
        username_input.clear()
        username_input.send_keys(self.username)

        password_input = self.__find('//*[@type="password"]')
        password_input.clear()
        password_input.send_keys(self.password)

        print("Aguardando login...")

        # Navegate to nanodeegree
        self.__wait_load('//*[contains(text(), "Fechar")]')
        modal_btn = self.__find('//button[text()="Fechar"]')
        modal_btn.click()

        ndeg_btn = self.__find('//a[text()="Acessar Modulos Nanodegree"]')
        ndeg_btn.click()

       # Change tab
        original_window = self.driver.current_window_handle
        WebDriverWait(self.driver, timeout=20000000000).until(
            EC.number_of_windows_to_be(2))

        for window_handle in self.driver.window_handles:
            if window_handle != original_window:
                self.driver.switch_to.window(window_handle)
                break

        # Get cookies session
        for cookie in self.driver.get_cookies():
            self.session.cookies.set(cookie['name'], cookie['value'])

    def get_data(self):
        course_data = []

        print("Navegue até a pagina do curso...")
        self.__wait_load('//ul[@id="js-course-tree-ajax"]/li')

        course_name = self.__find(
            '//div[@class="course-header-info"]//h2').text
        print(f"Extraindo informações do curso [{course_name}]...")

        classes = self.__find_all('//ul[@id="js-course-tree-ajax"]/li')
        for classroom in classes:
            classroom_id = classroom.get_attribute('data-id')
            classroom_name = classroom.text

            # Open and wait current clasroom, generate name and lessons.
            classroom.click()
            self.__wait_load(
                f'//li[@data-id={classroom_id}]//a[@class="lesson-title"]', time=5)

            # Get all lessons inside current classroom
            lessons_elm = self.__find_all(
                f'//li[@data-id={classroom_id}]//a[@class="lesson-title"]')

            classroom_lessons = [{"name": lesson.text, "url": lesson.get_attribute('href')}
                                 for lesson in lessons_elm]

            course_data.append({
                "class_name": classroom_name,
                "lessons": classroom_lessons,
            })

        return {"course_name": course_name, "data": course_data, "extension": "json"}

    def get_file(self, lesson_name, url, path):
        self.driver.get(url)

        try:
            self.driver.implicitly_wait(5)
        except:
            return {}

        # PDF
        if self.__find_all('//iframe[@title="PDF"]'):
            pdf_url = self.__find(
                '//iframe[@title="PDF"]').get_attribute("src").split('=')[1]
            url_parse = urllib.parse.unquote(pdf_url)

            print(f"Iniciando download do PDF [{lesson_name}]...")
            pdf = self.__download_pdf(url_parse)
            return {"data": pdf, "extension": "pdf"}

        # M3U8
        elif self.__find_all('//iframe'):
            self.driver.switch_to.frame(self.__find("//iframe"))
            try:
                m3u8_url = self.__find(
                    '//*[@id="my-video_html5_api"]').get_attribute("source")
                print(f"Iniciando download do video [{lesson_name}]...")
                self.__download_m3u8(m3u8_url, lesson_name, path)
            except:
                pass
            finally:
                return {}

        # ZIP
        if self.__find_all('//div[@class="download-player"]/a'):
            zip_url = self.__find(
                '//div[@class="download-player"]/a').get_attribute("href")
            zip_file = self.__download_zip(zip_url)
            return {"data": zip_file, "extension": "zip"}
        else:
            return {}

    def close(self):
        self.driver.quit()
