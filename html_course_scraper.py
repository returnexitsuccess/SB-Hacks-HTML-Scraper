import mechanize
import re
import json

def splitLines(html):
    lines = []
    lineStart = html.lower().find('<tr class="courseinforow">')
    lineEnd = html[lineStart + 1:].lower().find('<tr class="courseinforow">')
    i = 0
    while (lineEnd != -1):
        lineEnd += 1 + lineStart
        lines.append(html[lineStart:lineEnd])
        lineStart = lineEnd
        lineEnd = html[lineStart + 1:].lower().find('<tr class="courseinforow">')
        #print i
        #i += 1
    lineEnd = lineStart + 1 + html[lineStart + 1:].lower().find('</table>')
    lineEnd = lineEnd + 1 + html[lineEnd + 1:].lower().find('</table>')
    lineEnd = lineEnd + 1 + html[lineEnd + 1:].lower().find('</table>') #the third time will give the right index
    lines.append(html[lineStart:lineEnd])
    return lines

def lineToTable(dic, line):
    #check if class is cancelled
    indexStart = line.lower().find('class="status"')
    indexEnd = indexStart + 1 + line[indexStart + 1:].lower().find('</td>')
    if (line[indexStart:indexEnd].lower().find('cancelled') != -1):
        return dic

    indexStart = line.lower().find('<td style="text-align: left; vertical-align: middle;">') #instructor
    indexStart = indexStart + 1 + line[indexStart + 1:].lower().find('<td style="text-align: left; vertical-align: middle;">') #days
    indexEnd = indexStart + 1 + line[indexStart + 1:].lower().find('</td>')
    indexStart += line[indexStart:].lower().find('>') + 1
    days = line[indexStart:indexEnd].strip()

    indexStart = indexStart + 1 + line[indexStart + 1:].lower().find('<td style="text-align: left;') #time
    indexStart += line[indexStart:].lower().find('>') + 1
    indexEnd = indexStart + line[indexStart:].lower().find('</td>')
    time = line[indexStart:indexEnd].strip()

    indexStart = indexStart + 1 + line[indexStart + 1:].lower().find('<td style="text-align: left; vertical-align: middle;">') #room
    indexStart += line[indexStart:].lower().find('>') + 1
    indexEnd = indexStart + line[indexStart:].lower().find('</td>')
    s = line[indexStart:indexEnd].strip()
    if (s.lower() == "t b a"):
        return dic

    if (s.lower() == "musicllch"):
        roomNum = "LLCH"
        building = "MUSIC"
    else:
        n = re.search(" ", s)
        if n:
            numIndex = n.start()
            roomNum = s[numIndex:].strip()
            building = s[:numIndex].strip()
        else:
            m = re.search("\d", s)
            if m:
                numIndex = m.start()
                roomNum = s[numIndex:].strip()
                building = s[:numIndex].strip()
            else:
                roomNum = ""
                building = s.strip()
        if (building == ""):
            return dic

    indexStart = indexStart + 1 + line[indexStart + 1:].lower().find('<td style="text-align: right; vertical-align: middle;">')
    indexStart += line[indexStart:].lower().find('>') + 1
    indexEnd = indexStart + line[indexStart:].lower().find('</td>')
    maxsize = line[indexStart:indexEnd].strip().split()[2]

    try:
        dic[building][roomNum]
    except KeyError:
        try:
            dic[building]
        except KeyError:
            dic[building] = {roomNum: {c: {x/(2.0): False for x in range(16, 40)} for c in ['m','t','w','r','f']}}
        else:
            dic[building][roomNum] = {c: {x/(2.0): False for x in range(16, 40)} for c in ['m','t','w','r','f']}
        dic[building][roomNum]['size'] = maxsize

    for day in days.lower():
        if (day.isalpha()):
            d = dic[building][roomNum][day]
            dic[building][roomNum][day] = timeConvert(d, time)

    return dic

def timeConvert(dic, timeStr):
    time = []
    lastNumeric = False
    b = ""
    for c in timeStr:
        if (c.isdigit() and not lastNumeric):
            b = c
            lastNumeric = True
        elif (c.isdigit() and lastNumeric):
            b += c
        elif (not c.isdigit() and lastNumeric):
            lastNumeric = False
            time.append(b)
    
    start = int(time[0])
    if (start < 8):
        start += 12
    if (int(time[1]) >= 30):
        start += 0.5

    end = int(time[2])
    if (end < 8):
        end += 12
    if (int(time[3]) >= 30):
        end += 0.5

    i = start
    while (i <= end and i <= 19.5):
        dic[i] = True
        i += 0.5
    
    return dic

url = "https://my.sa.ucsb.edu/public/curriculum/coursesearch.aspx"
br = mechanize.Browser()
br.set_handle_robots(False)
br.open(url)
br.select_form(name="aspnetForm")
br.form["ctl00$pageContent$courseList"] = ["ANTH",]
br.form["ctl00$pageContent$quarterList"] = ["20151",]
br.form["ctl00$pageContent$dropDownCourseLevels"] = ["Undergraduate",]
res = br.submit()
content = res.read()

test = splitLines(content)
masterDict = {} #building -> room_num -> day_of_the_week -> time
for i in range(len(test)):
    masterDict = lineToTable(masterDict, test[i])

with open('data.json', 'wb') as fp:
    json.dump(masterDict, fp)
