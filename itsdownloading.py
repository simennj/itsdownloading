#! /usr/bin/env python3
import datetime
import sys
import traceback

import lxml.html
import os
import re
import requests


class Settings:
    def __init__(self):
        self.school = 'ntnu'
        self.base_url = 'https://{}.itslearning.com'.format(self.school)
        self.include_assignment_answers = False
        self.root_dir = os.path.abspath(os.path.join(os.path.curdir, 'Downloaded courses'))
        self.session = requests.Session()
        self.unnamed_counter = 0

    def set_school_and_base_url(self, school: str):
        self.school = school
        self.base_url = 'https://{}.itslearning.com'.format(self.school)

    def unnamed_count(self):
        self.unnamed_counter = self.unnamed_counter + 1
        return self.unnamed_counter


settings = Settings()
session = requests.Session()


def main():
    console_settings_init()
    console_login()
    selected_urls = console_select_urls()
    for selected_name, selected_url in selected_urls:
        try:
            download_course_or_project(selected_url)
        except Exception:
            print('failed to download the course/project {}'.format(selected_name))
            cur_dir = os.path.join(settings.root_dir, selected_name)
            file_path = os.path.join(cur_dir, 'errors.txt')
            print('saving error log to {}'.format(file_path))
            os.makedirs(cur_dir, exist_ok=True)
            with open(file_path, 'a') as file:
                file.write('\r\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\r\n')
                file.write('start error at {}\r\n'.format(datetime.datetime.now()))
                file.write(traceback.format_exc())
                file.write('\r\nend error at {}'.format(datetime.datetime.now()))
                file.write('\r\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\r\n')


def console_settings_init():
    if re.match('[hH].*', input('Choose ntnu or hist: ')):
        settings.set_school_and_base_url('hist')
    print('You chose ' + settings.school)
    if re.match('[yYjJ].*', input('Include assignment answers? y/n: ')):
        settings.include_assignment_answers = True
        print('Including assignment answers.')
    else:
        settings.include_assignment_answers = False
        print('Not including assignment answers.')
    new_path = input(
        'Current location is "{}".\r\n'
        'Type a new path to change it or just press enter to keep it:\r\n'.format(settings.root_dir))
    if new_path:
        settings.root_dir = new_path
    print('Path is set to "{}".'.format(settings.root_dir))


def console_login():
    import getpass
    logged_in = False
    while not logged_in:
        username = input('Username: ')
        print('No characters are shown while typing in a password in a terminal or cmd.')
        print('Just type in the password and press enter like normal, the window is not frozen.')
        password = getpass.getpass('Password: ')
        logged_in = attempt_login(username, password)
        if not logged_in:
            print('Wrong username or password.')


def attempt_login(username: str, password: str) -> bool:
    form = get_form_from_page(session.get('https://innsida.ntnu.no/lms-' + settings.school))
    login_url = 'https://idp.feide.no/simplesaml/module.php/feide/login.php' + form.action
    data = get_values_from_form(form)
    data['feidename'] = username.lower()
    data['password'] = password
    confirm_login_page = session.post(login_url, data=data)
    logged_in = confirm_login(confirm_login_page)
    return logged_in


def get_form_from_page(page: requests.Response) -> lxml.html.FormElement:
    tree = lxml.html.fromstring(page.content)
    form = tree.forms[0]
    if form.xpath('fieldset/select[@name="org"]'):
        page = session.get(page.url + '&org=ntnu.no')
        return get_form_from_page(page)
    return form


def get_values_from_form(form: lxml.html.FormElement) -> dict:
    return {i.xpath("@name")[0]: i.xpath("@value")[0] for i in form.xpath(".//input[@name]") if i.xpath("@value")}


def confirm_login(confirm_login_page: requests.Response) -> bool:
    form = get_form_from_page(confirm_login_page)
    try:
        session.post(form.action, get_values_from_form(form))
    except requests.exceptions.MissingSchema:
        return False
    if settings.school == 'hist':
        hist_extra_login(confirm_login_page)
    return True


def hist_extra_login(confirm_login_page: requests.Response):
    confirm_login_page2 = post_form_from_page(confirm_login_page)
    confirm_login_page3 = post_form_from_page(confirm_login_page2)
    tree = lxml.html.fromstring(confirm_login_page3.content)
    try:
        data = {
            '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$federatedLoginButtons$ctl00$ctl00',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': tree.xpath('//input[@name="__VIEWSTATE"]/@value')[0],
            '__VIEWSTATEGENERATOR': '90059987',
            '__EVENTVALIDATION': tree.xpath('//input[@name="__EVENTVALIDATION"]/@value')[0],
            'ctl00$ContentPlaceHolder1$Username$input': '',
            'ctl00$ContentPlaceHolder1$Password$input': '',
            'ctl00$ContentPlaceHolder1$showNativeLoginValueField': '',
            'ctl00$language_internal$H': '0'
        }
        page = session.post('https://hist.itslearning.com/Index.aspx', data=data)
        confirm_login_page4 = post_form_from_page(page)
        post_form_from_page(confirm_login_page4)
    except IndexError:
        with open(os.path.join(settings.root_dir, 'login_error.html'), 'wb') as file:
            file.write(confirm_login_page3.content)
        print('Login process seems to have failed on the page saved as login_error.html')
        print('\r\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\r\n')
        print(traceback.format_exc())
        print('\r\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\r\n')
        print('Trying to continue anyway (if no courses are shown, the login failed)')


def post_form_from_page(page: requests.Response) -> requests.Response:
    form = get_form_from_page(page)
    return session.post(form.action, get_values_from_form(form))


def console_select_urls() -> list:
    choices = get_courses_and_projects()
    names = list(choices)
    print('Found the following favorite courses and projects:')
    for index, course_name in enumerate(names):
        print('{}: {}'.format(index, course_name))
    print('all: all')
    answer = input('List the ones you want to download. Eg. 2 5 6 7 12 3. Or type all\n: ')
    if answer == 'all':
        selected_urls = list(choices.items())
    else:
        selected_urls = [(names[int(i)], choices[names[int(i)]]) for i in answer.split()]
    return selected_urls


def get_courses_and_projects() -> dict:
    courses = get_courses()
    projects = get_projects()
    return {
        **{
            course_name: settings.base_url + "/main.aspx?CourseID=" + course_id
            for course_name, course_id in courses.items()
        },
        **{
            project_name: settings.base_url + "/main.aspx?ProjectID=" + project_id
            for project_name, project_id in projects.items()
        }
    }


def get_courses() -> dict:
    return retrieve_topmenu_list(settings.base_url + "/TopMenu/TopMenu/GetCourses")


def get_projects() -> dict:
    return retrieve_topmenu_list(settings.base_url + "/TopMenu/TopMenu/GetProjects")


def retrieve_topmenu_list(url: str) -> dict:
    page = session.get(url)
    tree = lxml.html.fromstring(page.content)
    return {
        item.xpath('@data-title')[0]: item.xpath('a/@href')[0].split('=')[-1]
        for item in tree.xpath('//li')
        if item.xpath('@data-title') and item.xpath('a/@href')
    }


def download_course_or_project(url: str):
    page = session.get(url)
    url = page.url
    tree = lxml.html.fromstring(page.content)
    folder_id = re.search('var contentAreaRootFolderId = \"item\" \+ ([0-9]+);',
                          tree.xpath('//aside/script')[0].text).groups()[0]
    title = tree.xpath('//h1[@class="treemenu-title"]/span/text()')[0]
    directory = os.path.join(settings.root_dir, title)
    download_folder(directory, url, folder_id)


def download_folder(directory: str, url: str, folder_id: str, excluded_folders: set = set()):
    page = session.get('{}&id=item{}'.format(url, folder_id))
    tree = lxml.html.fromstring(page.content)
    os.makedirs(directory, exist_ok=True)
    for link_element in tree.xpath('//a'):
        link_type, link_tail = link_element.xpath('@href')[0].split('/')[-2:]
        link_url = '{}/{}/{}'.format(settings.base_url, link_type, link_tail)
        link_name = "".join(char if char.isalnum() else '_' for char in link_element.xpath('.//text()')[0].strip())
        if link_type == 'Folder' or link_type == 'ContentArea':
            excluded_folders.add(folder_id)
            new_directory = os.path.join(directory, link_name)
            folder_id = re.search('FolderID=([0-9]+)', link_tail).groups()[0]
            if folder_id not in excluded_folders:
                download_folder(new_directory, url, folder_id, excluded_folders)
        elif link_type == 'File':
            download_from_file_page(directory, link_url)
        elif link_type == 'essay':
            download_from_essay_page(directory, link_url)
        elif link_type == 'note':
            save_as_html(directory, link_url, link_name)
        elif link_type == 'LearningToolElement':
            save_link(directory, link_url, link_name)
        elif link_type == '':
            pass
        else:
            print('Will not download: {}, (is a {})'.format(os.path.join(directory, link_name), link_type))


def save_as_html(directory: str, link_url: str, name: str):
    page_to_download = session.get(link_url).content
    with open(os.path.join(directory, name + '.html'), 'wb') as downloaded_file:
        downloaded_file.write(page_to_download)
    print('Saved {} as a html file'.format(os.path.join(directory, name)))


def save_link(directory: str, link_url: str, name: str):
    tree = get_tree(get_tree(link_url).xpath('//iframe/@src')[0])
    try:
        link = tree.xpath('//section[@class="file-link-link"]/a')[0]
    except IndexError:
        print("could not find download link in page {}, downloading page instead.".format(link_url))
        save_as_html(directory, link_url, name)
        return
    if 'download' in link.keys():
        download_file(directory, link.get('href'))
    else:
        with open(os.path.join(directory, name + '.txt'), 'w') as downloaded_file:
            downloaded_file.write(link.get('href'))
        print('Saved {} as a html file'.format(os.path.join(directory, name)))


def get_tree(url):
    return lxml.html.fromstring(session.get(url).content)


def download_from_essay_page(directory: str, link_url: str):
    essay_page = session.get(link_url)
    tree = lxml.html.fromstring(essay_page.content)
    download_urls = tree.xpath(
        '//div[@id="EssayDetailedInformation_FileListWrapper_FileList"]/ul/li/a/@href')
    if settings.include_assignment_answers:
        download_urls += tree.xpath('//div[@id="DF_FileList"]/ul/li/a[@class="ccl-iconlink"]/@href')
    for download_url in download_urls:
        download_file(directory, download_url)


def download_from_file_page(directory: str, link_url: str):
    try:
        file_page = session.get(link_url)
        download_url = settings.base_url + lxml.html.fromstring(file_page.content).xpath(
            '//a[@class="ccl-button ccl-button-color-green ccl-button-submit"]/@href'
        )[0][2:]
    except Exception:
        print('failed to download the file from {} in {}'.format(link_url, directory))
        file_path = os.path.join(directory, 'errors.txt')
        print('saving error log to {}'.format(file_path))
        with open(file_path, 'a') as file:
            file.write('\r\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\r\n')
            file.write('start error from {} in {} at {}\r\n'.format(link_url, directory, datetime.datetime.now()))
            file.write(traceback.format_exc())
            file.write('\r\nend error from {} in {} at {}'.format(link_url, directory, datetime.datetime.now()))
            file.write('\r\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\r\n')
        return
    download_file(directory, download_url)


def download_file(directory: str, download_url: str):
    try:
        download = session.get(download_url, stream=True)
        try:
            content_disposition = download.headers['content-disposition']
            raw_file_name = re.findall('filename="(.+)"', content_disposition)[0]
        except Exception:
            print('The file from {} in {} does not seem to have a name. Saving as unnamed{}.txt'.format(download_url,
                                                                                                        directory,
                                                                                                        settings.unnamed_counter))
            raw_file_name = 'unnamed{}.txt'.format(settings.unnamed_count)
        filename = raw_file_name.encode('iso-8859-1').decode()
        filepath = os.path.join(directory, filename)
        with open(filepath, 'wb') as downloaded_file:
            for chunk in download:
                downloaded_file.write(chunk)
        print('Downloaded: ', filepath)
    except Exception:
        print('failed to download the file from {} in {}'.format(download_url, directory))
        file_path = os.path.join(directory, 'errors.txt')
        print('saving error log to {}'.format(file_path))
        with open(file_path, 'a') as file:
            file.write('\r\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\r\n')
            file.write('start error from {} in {} at {}\r\n'.format(download_url, directory, datetime.datetime.now()))
            file.write(traceback.format_exc())
            file.write('\r\nend error from {} in {} at {}'.format(download_url, directory, datetime.datetime.now()))
            file.write('\r\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\r\n')


if __name__ == '__main__':
    if sys.version_info.major == 3 and sys.version_info.minor >= 5:
        main()
    else:
        print('This script is made for python 3.5 (or later)')
