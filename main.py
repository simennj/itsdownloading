import requests
from lxml.html import fromstring


def login():
    page = session.get('https://sats.itea.ntnu.no/sso-wrapper/web/wrapper?target=itslearning')
    tree = fromstring(page.content)
    form = tree.forms[0]
    form.inputs['feidename'].value = ''
    form.inputs['password'].value = ''
    data = {i.xpath("@name")[0]: i.xpath("@value")[0] for i in form.xpath(".//input[@name]")}
    form.action = 'https://idp.feide.no/simplesaml/module.php/feide/login.php' + form.action
    return session.post(form.action, data=data)


def confirm_login():
    tree = fromstring(confirm_login_page.content)
    form = tree.forms[0]
    data = {i.xpath("@name")[0]: i.xpath("@value")[0] for i in form.xpath(".//input[@name]") if i.xpath("@value")}
    return session.post("https://sats.itea.ntnu.no/sso-wrapper/feidelogin", data=data)


with requests.Session() as session:
    confirm_login_page = login()
    with open('login_page2.html', 'wb') as file:
        file.write(confirm_login_page.content)
    its_page = confirm_login()
    with open('its_page.html', 'wb') as file:
        file.write(its_page.content)
    courses = session.get("https://ntnu.itslearning.com/TopMenu/TopMenu/GetCourses")
    with open('courses.html', 'wb') as file:
        file.write(courses.content)
