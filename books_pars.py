import time
import config

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup as bs
from ebooklib import epub

book = epub.EpubBook()

driver = webdriver.Chrome()
driver.get(config.main_url)


# Авторизуемся на АТ с заданными логином и паролем
def auth():
    driver.find_element_by_xpath('//a[@onclick="app.showLoginModal();"]').click()
    time.sleep(1)
    driver.find_element_by_xpath('//*[@id="authModal"]/div/div/div[2]/div/div/div/div/form/button[1]').click()

    login = driver.find_element_by_xpath('//*[@id="login_submit"]/div/div/input[6]')
    time.sleep(2)
    login.click()
    login.send_keys(config.login)

    pswd = driver.find_element_by_xpath('//*[@id="login_submit"]/div/div/input[7]')
    pswd.send_keys(config.pswd)

    driver.find_element_by_xpath('//*[@id="install_allow"]').click()


auth()

driver.get(config.main_url)
time.sleep(3)

# Переходим на страницу читалки
driver.find_element_by_xpath('//*[@id="pjax-container"]/section/div/div/div[1]/div[1]/div/div/div[1]/a').click()

# Переходим к первой главе
driver.execute_script('document.querySelector("#app > aside > div.contents > ul > li:nth-child(1)").click()')

# Добавляем в формируемую книгу обязательные тэги
soup = bs(driver.page_source, 'lxml')
time.sleep(1)
author_name = soup.find('div', class_='book-author').text
book_name = soup.find('div', class_='book-title').text

book.set_identifier('test id')
book.set_title(book_name)
book.set_language('en')

book.add_author(author_name)

# Переход по страницам и сохранение информации. Основной цикл.
# Количество глав включая пролог и эпилог. -2 это костыль :(
chapter_col = len(driver.find_elements_by_xpath("//ul//li")) - 2
book.spine = ['nav']
for i in range(chapter_col):

    time.sleep(2)
    soup = bs(driver.page_source, 'lxml')

    # Преобразуем текст главы из "списка" в "строку"
    chapter_text = '\n'.join(str(line) for line in soup.find_all('p'))
    chapter_name = soup.find('h1').text
    try:
        driver.find_element_by_xpath('//a[@data-bind="click: goToChapter.bind($data, nextChapter())"]')
    except NoSuchElementException:
        print('Страницы кончились')
        break
    c = epub.EpubHtml(title=str(chapter_name), file_name='c' + str(i) + '.xhtml', lang='en')
    c.content = str(soup.find('h1')) + '\n' + chapter_text

    book.add_item(c)
    book.toc.append(epub.Link(str(c.file_name), str(chapter_name), str(chapter_name)))
    book.spine.append(c)

    driver.find_element_by_xpath('//a[@data-bind="click: goToChapter.bind($data, nextChapter())"]').click()


book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())


if __name__ == '__main__':
    epub.write_epub('1.epub', book, {})
