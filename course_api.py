from bs4 import BeautifulSoup
import math
import requests
import sys


def parse_course_title(soup):
    title = soup.h4.string
    return title.split('(')[0].strip()


def parse_course_teachers(soup):
    urls = set({})
    teachers = []
    for row in soup.find(id='VkOnderwijsteam1_lblContent').table.children:
        if row.a is not None and row.a['href'] not in urls:
            url = row.a['href']
            urls.add(url)
            email = url.split('email=')[1] + "@uhasselt.be"
            teachers.append({'name': row.a.string.strip(), 'email': email, 'url': url})
    return teachers


def parse_course_language(soup):
    return soup.find(id='VkOnderwijstaal1_lblContent').b.string.strip()


def parse_course_prerequisites(soup):
    item = soup.find(id='VkFicheVolgt1_lblContent').table.table
    if item is None:
        return []
    
    prerequisites = []
    for td in item.find_all('td'):
        if td.string is not None and td.string.find('(') != -1 and td.string.find(')') != -1:
            parts = td.string.split('(')
            id = parts[1].split(')')[0]
            prerequisites.append({'title': parts[0].strip(), 'id': id})
    return prerequisites


def parse_course_semester(soup):
    for it in soup.find_all('td'):
        try:
            if it['id'].find('P1SP') >= 0:
                return 1
            elif it['id'].find('P2SP') >= 0:
                return 2
        except:
            continue
    return math.nan


def parse_course_credits(soup):
    for it in soup.find_all('td'):
        try:
            if it['id'].find('0RSp') >= 0:
                return int(float(it.string.replace(',', '.')))
        except:
            continue
    return math.nan


def parse_course_content(soup):
    return soup.find(id='VkSgteam1_ctl03_gvContent').td.get_text()


class Course:
    def __init__(self, id, name, url, language, education_team, prerequisites, semester, credits, content):
        self.id = id
        self.name = name
        self.url = url
        self.language = language
        self.education_team = education_team
        self.prerequisites = prerequisites
        self.semester = semester
        self.credits = credits
        self.content = content


def parse_course(id):
    url = 'https://uhintra03.uhasselt.be/studiegidswww/opleidingsonderdeel.aspx?a=2020&i=%s&n=4&t=01' % id
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    
    return Course(
        id = id,
        name = parse_course_title(soup),
        url = url,
        education_team = parse_course_teachers(soup),
        language = parse_course_language(soup),
        prerequisites = parse_course_prerequisites(soup),
        semester = parse_course_semester(soup),
        credits = parse_course_credits(soup),
        content = parse_course_content(soup)
    )


def list_all_courses():
    url = 'https://uhintra03.uhasselt.be/studiegidswww/opleidingsonderdeel.aspx'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    courses = []
    for select in soup.find_all('select'):
        if select['name'] == 'beschridDDL$ctl00':
            for option in select.find_all('option'):
                if option['value'] != '':
                    id = option['value']
                    name = option.string.split('(')[0].strip()
                    courses.append({'id': id, 'name': name, 'searchname': name.casefold()})
            break
    return courses

if __name__ == '__main__':
    courses = list_all_courses()
    req = sys.argv[1].strip().casefold()
    req_course = None
    for course in courses:
        if course['searchname'] == req:
            req_course = course
            break

    if req_course is None:
        print("Unknown course: %s" % req)
    else:
        print("Course: %s (%s)" % (req_course.name, req_course.id))
        info = parse_course(req_course.id)
        for key in info:
            print("%s: %s" % (key, info[key]))
