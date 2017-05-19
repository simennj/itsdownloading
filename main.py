#! /usr/bin/env python3
import re

import os
import sys
from lxml.html import fromstring


def main():
    import requests
    with requests.Session() as session:
        feide_login(session)
        selected_urls = select_urls(session)
        for selected_url in selected_urls:
            page = session.get(selected_url)
            url = page.url
            tree = fromstring(page.content)
            folder_id = re.search('var contentAreaRootFolderId = \"item\" \+ ([0-9]+);',
                                  tree.xpath('//aside/script')[0].text).groups()[0]
            title = tree.xpath('//h1[@class="treemenu-title"]/span/text()')[0]
            directory = os.path.join(os.path.curdir, 'Downloaded courses', title)
            download_folder(directory, url, folder_id, session)


def feide_login(session):
    logged_in = False
    while not logged_in:
        page = session.get('https://sats.itea.ntnu.no/sso-wrapper/web/wrapper?target=itslearning')
        form = get_form_from_page(page)
        form = fill_login_form(form)
        login_url = 'https://idp.feide.no/simplesaml/module.php/feide/login.php' + form.action
        data = get_values_from_form(form)
        confirm_login_page = session.post(login_url, data=data)
        logged_in = confirm_login(session, confirm_login_page)


def get_form_from_page(page):
    tree = fromstring(page.content)
    return tree.forms[0]


def fill_login_form(form):
    import getpass
    form.inputs['feidename'].value = input('Brukernavn: ')
    form.inputs['password'].value = getpass.getpass('Passord: ')
    return form


def get_values_from_form(form):
    return {i.xpath("@name")[0]: i.xpath("@value")[0] for i in form.xpath(".//input[@name]") if i.xpath("@value")}


def confirm_login(session, confirm_login_page):
    form = get_form_from_page(confirm_login_page)
    return session.post("https://sats.itea.ntnu.no/sso-wrapper/feidelogin",
                        data=get_values_from_form(form)).content != b'Required parameter RelayState not found.'


def select_urls(session):
    choices = get_courses_and_projects(session)
    names = list(choices)
    print('Found the following favorite courses and projects:')
    for index, course_name in enumerate(names):
        print('{}: {}'.format(index, course_name))
    print('all: all')
    answer = input('List the ones you want to download. Eg. 2 5 6 7 12 3. Or type all\n: ')
    if answer == 'all':
        selected_urls = choices.values()
    else:
        selected_urls = [choices[names[int(i)]] for i in answer.split()]
    return selected_urls


def get_courses_and_projects(session):
    courses = get_courses(session)
    projects = get_projects(session)
    return {
        **{
            course_name: "https://ntnu.itslearning.com/main.aspx?CourseID=" + course_id
            for course_name, course_id in courses.items()
        },
        **{
            project_name: "https://ntnu.itslearning.com/main.aspx?ProjectID=" + project_id
            for project_name, project_id in projects.items()
        }
    }


def get_courses(session):
    courses = retrieve_topmenu_list(session, "https://ntnu.itslearning.com/TopMenu/TopMenu/GetCourses")
    return courses


def get_projects(session):
    projects = retrieve_topmenu_list(session, "https://ntnu.itslearning.com/TopMenu/TopMenu/GetProjects")
    return projects


def retrieve_topmenu_list(session, url):
    page = session.get(url)
    tree = fromstring(page.content)
    return {
        item.xpath('@data-title')[0]: item.xpath('a/@href')[0].split('=')[-1]
        for item in filter(lambda item: item.xpath('@data-title') and item.xpath('a/@href'), [item for item in tree.xpath('//li')])
    }


def download_folder(directory, url, folder_id, session):
    page = session.get('{}&id=item{}'.format(url, folder_id))
    tree = fromstring(page.content)
    os.makedirs(directory, exist_ok=True)
    for link_element in tree.xpath('//a'):
        link_type, link_tail = link_element.xpath('@href')[0].split('/')[-2:]
        link_url = 'https://ntnu.itslearning.com/{}/{}'.format(link_type, link_tail)
        link_name = "".join(char if char.isalnum() else '_' for char in link_element.xpath('.//text()')[0].strip())
        if link_type == 'Folder':
            new_directory = os.path.join(directory, link_name)
            folder_id = re.search('FolderID=([0-9]+)', link_tail).groups()[0]
            download_folder(new_directory, url, folder_id, session)
        elif link_type == 'File':
            download_file(directory, link_url, session)
        elif link_type == 'essay':
            download_essay(directory, link_url, session)
        elif link_type == 'note':
            save_note_as_html(directory, link_url, session, link_name)
        elif link_type == 'LearningToolElement':
            save_links_as_html(directory, link_url, session, link_name)
        elif link_type == '':
            pass
        else:
            print('Will not download: {}, (is a {})'.format(os.path.join(directory, link_name), link_type))


def save_note_as_html(directory, link_url, session, name):
    page_to_download = session.get(link_url).content
    with open(os.path.join(directory, name + '.html'), 'wb') as downloaded_file:
        downloaded_file.write(page_to_download)
    print('Saved {} as a html file'.format(os.path.join(directory, name)))


def save_links_as_html(directory, link_url, session, name):
    page = session.get(link_url)
    tree = fromstring(page.content)
    url = tree.xpath('//iframe/@src')[0]
    page_to_download = session.get(url).content
    with open(os.path.join(directory, name + '.html'), 'wb') as downloaded_file:
        downloaded_file.write(page_to_download)
    print('Saved {} as a html file'.format(os.path.join(directory, name)))


def download_essay(directory, link_url, session):
    essay_page = session.get(link_url)
    download_urls = fromstring(essay_page.content).xpath(
        '//div[@id="EssayDetailedInformation_FileListWrapper_FileList"]/ul/li/a/@href')
    for download_url in download_urls:
        download = session.get(download_url, stream=True)
        filepath = os.path.join(directory,
                                re.findall('filename="(.+)"', download.headers['content-disposition'])[0])
        with open(filepath, 'wb') as downloaded_file:
            for chunk in download:
                downloaded_file.write(chunk)
        print('Downloaded: ', filepath)


def download_file(directory, link_url, session):
    file_page = session.get(link_url)
    download_url = 'https://ntnu.itslearning.com' + \
                   fromstring(file_page.content).xpath(
                       '//a[@class="ccl-button ccl-button-color-green ccl-button-submit"]/@href')[0][2:]
    download = session.get(download_url, stream=True)
    raw_file_name = re.findall('filename="(.+)"', download.headers['content-disposition'])
    if raw_file_name:
        raw_file_name = raw_file_name[0]
    else:
        return
    filename = raw_file_name.encode('iso-8859-1').decode()
    filepath = os.path.join(directory, filename)
    with open(filepath, 'wb') as downloaded_file:
        for chunk in download:
            downloaded_file.write(chunk)
    print('Downloaded: ', filepath)

if sys.version_info.major == 3 and sys.version_info.minor >= 6:
    main()
else:
    print('This script is made for python 3.6 (or higher)')
