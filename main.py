from re import findall
import requests
from lxml.html import fromstring
from os import path, mkdir


def login():
    from getpass import getpass
    page = session.get('https://sats.itea.ntnu.no/sso-wrapper/web/wrapper?target=itslearning')
    tree = fromstring(page.content)
    form = tree.forms[0]
    form.inputs['feidename'].value = input('Brukernavn: ')
    form.inputs['password'].value = getpass('Passord: ')
    data = {i.xpath("@name")[0]: i.xpath("@value")[0] for i in form.xpath(".//input[@name]")}
    form.action = 'https://idp.feide.no/simplesaml/module.php/feide/login.php' + form.action
    return session.post(form.action, data=data)


def confirm_login():
    tree = fromstring(confirm_login_page.content)
    form = tree.forms[0]
    data = {i.xpath("@name")[0]: i.xpath("@value")[0] for i in form.xpath(".//input[@name]") if i.xpath("@value")}
    return session.post("https://sats.itea.ntnu.no/sso-wrapper/feidelogin", data=data)


def select_course():
    courses_page = session.get("https://ntnu.itslearning.com/TopMenu/TopMenu/GetCourses")
    tree = fromstring(courses_page.content)
    courses = {course.xpath('@data-title')[0]: course.xpath('a/@href')[0].split('=')[-1]
               for course in tree.xpath('//li')}
    course_names = list(courses)
    for index, course_name in enumerate(course_names):
        print('{}: {}'.format(index, course_name))
    selected_course = courses[course_names[int(input('Choose course (index): '))]]
    return session.get(
        'https://ntnu.itslearning.com/Status/PersonalStatus.aspx?CourseID={}&PersonId={}'.format(
            selected_course,
            user_id
        )
    )


def download_content():
    tree = fromstring(contents_page.content)
    course_name = tree.xpath('//tr[@id="row_0"]/td/span/text()')[0].strip()
    current_indent = 0
    current_dir = path.join(path.curdir, course_name)
    if not path.exists(current_dir):
        mkdir(current_dir)
    for element in tree.xpath('//td[@headers="personal_report_list_header_subject" and text()]'):
        indent = element.xpath('./text()')[0].count('\xa0') // 7
        _, element_type, url = element.xpath('a/@href')[0].split('/')
        name = element.xpath('a/span/text()')[0]
        while indent <= current_indent:
            current_dir, _ = path.split(current_dir)
            current_indent -= 1
        if element_type == 'folder':
            name = "".join(char if char.isalnum() else '_' for char in name).strip()
            current_dir = path.join(current_dir, name)
            current_indent += 1
            if not path.exists(current_dir):
                mkdir(current_dir)
        elif element_type == 'file':
            file_page = session.get('https://ntnu.itslearning.com/{}/{}'.format(element_type, url))
            download_url = 'https://ntnu.itslearning.com' + \
                           fromstring(file_page.content).xpath('//a[@title="Download"]/@href')[0][2:]
            download = session.get(download_url, stream=True)
            raw_file_name = findall('filename="(.+)"', download.headers['content-disposition'])[0]
            filename = raw_file_name.encode('iso-8859-1').decode()
            filepath = path.join(current_dir, filename)
            with open(filepath, 'wb') as download_file:
                for chunk in download:
                    download_file.write(chunk)
            print('Downloaded: ', filepath)
        elif element_type == 'essay':
            essay_page = session.get('https://ntnu.itslearning.com/{}/{}'.format(element_type, url))
            download_urls = fromstring(essay_page.content).xpath(
                '//div[@id="EssayDetailedInformation_FileListWrapper_FileList"]/ul/li/a/@href')
            for download_url in download_urls:
                download = session.get(download_url, stream=True)
                filepath = path.join(current_dir,
                                     findall('filename="(.+)"', download.headers['content-disposition'])[0])
                with open(filepath, 'wb') as download_file:
                    for chunk in download:
                        download_file.write(chunk)
                print('Downloaded: ', filepath)
        elif element_type == 'note' or element_type == 'LearningToolElement':
            page_to_download = session.get('https://ntnu.itslearning.com/{}/{}'.format(element_type, url)).content
            name = "".join(char if char.isalnum() else '_' for char in name).strip()
            with open(path.join(current_dir, name + '.html'), 'wb') as download_file:
                download_file.write(page_to_download)
            print('Saved {} as a html file'.format(path.join(current_dir, name)))
        else:
            print('Will not download: {}, (is a {})'.format(path.join(current_dir, name), element_type))


with requests.Session() as session:
    confirm_login_page = login()
    home_page = confirm_login()
    user_id = fromstring(home_page.content).xpath('//@data-personid')[0]
    contents_page = select_course()
    download_content()
