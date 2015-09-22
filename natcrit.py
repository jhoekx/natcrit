#!/usr/bin/env python2

import re

import html5lib

from html5lib import treebuilders
from xml.etree import cElementTree

from mako.template import Template

# namespaceHTMLElements=False: work around bug in html5lib 0.90
parser = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("etree", cElementTree),namespaceHTMLElements=False)

# Ranking events
#competitions = ["20110327", "20110417md", "20110522", "20110703", "20110904", "20110911", "20110918md", "20111002last"]
#competitions = [ "20120226", "20120304md", "20120318", "20120325", "20120415md", "20120909",
#"20120916", "20121007last" ]
#competitions = ["20120304md"]
#competitions = [ "20130224", "20130303", "20130324", "20130407", "20130623", "20130825", "20130908", "20130915last" ]
#competitions = ["20140223", "20140302", "20140323", "20140427", "20140511", "20140914", "20140928", "20141019last"]
competitions = ["20150222", "20150301", "20150308", "20150412", "20150621", "20150829", "20150830", "20150913last"]
max_count = 6

# scoring lists
points = [30, 27, 25, 23, 21, 19, 17, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
lastpoints = [45, 40, 37, 35, 32, 29, 26, 23, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]

# whitelisted clubs
club_whitelist = [u'Omega', u'hamok', u'O.L.G. St. Vith "ARDOC"', u'O.L.G. St. Vith ARDOC', u'TROL', u'B.A.B.A.', u'ASUB', u'C.O. Li\xe8ge', u'C.O.M.B.', u'C.O. P\xe9gase', u'Hermathenae', u'K.O.L.', u'Alta\xefr C.O.', u'O.L.V. Eifel', u'Borasca', u'N.S.V. Amel', u'Balise 10', u'Hainaut O.C.', u'H.O.C.',u'C.L.O. Chiny',u'Les Raptors', u'C.O. Militaire Belge', u'E.P.O.S.']

# club mapping
club_mapping = {
    u'O.L.G. St. Vith ARDOC': u'O.L.G. St. Vith "ARDOC"',
    u'P\xe9gase': u'C.O. P\xe9gase',
    u'O.L.V.E.': u'O.L.V. Eifel'
}

# whitelisted categories
categories = ['D-10', 'D-12', 'D-14', 'D-16', 'D-18', 'D-20', 'DE', 'D21', 'DB', 'D35', 'D40', 'D45', 'D50', 'D55', 'D60', 'D65', 'D70', 'D75', 'D80', 'D85', 'H-10', 'H-12', 'H-14', 'H-16', 'H-18', 'H-20', 'HE', 'H21', 'HB', 'H35', 'H40', 'H45', 'H50', 'H55', 'H60', 'H65', 'H70', 'H75', 'H80', 'H85']

md_mapping = {
    "D. Pupilles": ["D-12", "D-10"],
    "D. Espoirs": ["D-16", "D-14"],
    "D. Juniores": ["D-20", "D-18"],
    "D. Junioren": ["D-20", "D-18"],
    "D. Open": ["DE", "D35", "D21", "DB"],
    "D. Masters A": ["D40", "D45"],
    "D. Masters B": ["D50", "D55"],
    "D. Masters C": ["D60", "D65"],
    "D. Masters D": ["D70", "D75", "D80", "D85"],
    "H. Pupilles": ["H-12", "H-10"],
    "H. Espoirs": ["H-16", "H-14"],
    "H. Juniors": ["H-20", "H-18"],
    "H. Junioren": ["H-20", "H-18"],
    "H. Open": ["HE", "H35", "H21", "HB"],
    "H. Masters A": ["H40", "H45"],
    "H. Masters B": ["H50", "H55"],
    "H. Masters C": ["H60", "H65"],
    "H. Masters D": ["H70", "H75", "H80", "H85"],
    }

# Helper classes
class Event:
    name = None
    categories = None
    
    # special regularity fields
    is_middle = False
    is_last = False
    
    def __init__(self):
        self.categories = []
    
    def to_text(self):
        ret=[]
        
        for category in self.categories:
            ret.append("Category %s"%(category.name))
            for result in category.results:
                ret.append("%s %s %s %s"%(result.name, result.club, result.time, result.score))
        
        return "\n".join(ret)

class Category:
    name = None
    results = None
    
    def __init__(self):
        self.results = []
    
    """ Map this category to a list of possible categories in a middle distance
        race """
    def get_md_mapping(self):
        for k,v in md_mapping.items():
            if k in self.name:
                return v

class Result:
    name = None
    club = None
    time = None
    score = None
    
    def __str__(self):
        return "%s %s %s"%(self.name, self.club, self.time)

class Runner:
    name = None
    club = None
    place = None
    total = None
    results = None
    data = None
    def __init__(self):
        self.results = []
        self.data = []

events = []

for competition in competitions:
    # competitions have the following form:
    # yyyymmdd[md][last]
    event = Event()
    events.append(event)
    
    date = competition[0:8]
    
    event.name = date
    if "md" in competition:
        event.is_middle = True
    if "last" in competition:
        event.is_last = True

    # Parse result list into a data structure
    with open("data/"+date+".htm") as f:
        print "Now processing %s"%(date)
        currentCategory = None
        
        root = parser.parse(f)
        table = root.find(".//table[@class='ph']")
        rows = table.findall(".//tr")
        for row in rows:
            # row can be a heading, a result or nonsense
            heading = row.find(".//h2")
            if heading is not None:
                category = Category()
                category.name = heading[0].text.strip()
                
                currentCategory = category
                event.categories.append( category )
                continue
            
            cells = row.findall(".//td")
            # 8 children: webres
            # 5 children: normal page, no nationality
            # 6 children: normal page
            # 9 children: new webres (2011/07/04)
            # 10 children: newer webres (2015/03/28)
            if len(cells) == 8 or len(cells) == 6 or len(cells) == 5 or len(cells) == 9 or len(cells) == 10:
                place = cells[0].text
                
                # basic result
                result = Result()
                if len(cells) == 8 or len(cells) == 9:
                    if len(cells[2]) == 0:
                        # this skips decorative rows in new webres
                        continue
                    result.name = cells[2][0].text
                    result.club = cells[5][0].text
                    time = cells[6].text
                elif len(cells) == 10:
                    if len(cells[2]) == 0:
                        # this skips decorative rows in new webres
                        continue
                    result.name = cells[2][0].text
                    result.club = cells[6][0].text
                    time = cells[7].text
                elif len(cells) == 6:
                    result.name = cells[1].text
                    result.club = cells[3].text
                    time = cells[4].text
                elif len(cells) == 5:
                    result.name = cells[1].text
                    result.club = cells[2].text
                    time = cells[3].text
                # transform the time to seconds
                if time is None:
                    continue
                parts = re.match("([0-9]+):([0-9]+):([0-9]+)|([0-9]+):([0-9]+)",time)
                try:
                    if parts.group(1) is not None:
                        pass
                except:
                    continue
                if parts.group(1) is not None:
                    # hh:mm:ss
                    hours = int(parts.group(1))
                    minutes = int(parts.group(2))
                    seconds = int(parts.group(3))
                elif parts.group(4) is not None:
                    # mm:ss
                    hours = 0
                    minutes = int(parts.group(4))
                    seconds = int(parts.group(5))
                else:
                    # no valid time, means not a valid runner
                    continue
                result.time = (hours*60 + minutes)*60 + seconds

                if result.club in club_mapping:
                    result.club = club_mapping[result.club]

                currentCategory.results.append(result)
                continue

# Map middle distance races to normal categories
# rule: a runner will be ranked in the highest category where he participated in

# Generate a category<->runner mapping for all non-md races
category_runner = {}
for category in categories:
    category_runner[category] = []
for event in events:
    if event.is_middle:
        continue
    
    for category in event.categories:
        if category.name not in categories:
            continue
        for result in category.results:
            if result.name not in category_runner[category.name]:
                category_runner[category.name].append(result.name)
# create the standard categories for all md events
for event in events:
    if event.is_middle:
        for name in categories:
            category = Category()
            category.name = name
            event.categories.append(category)
# Rank runners in the expected category
for event in events:
    if not event.is_middle:
        continue
    for category in event.categories:
        possible_categories = category.get_md_mapping()
        if possible_categories is None:
            print "MD: drop %s"%(category.name)
            continue
        for result in category.results:
            has_mapped = False
            for mapping in possible_categories:
                if result.name in category_runner[mapping]:
                    # "mapping" is the category where the runner will be ranked
                    target = [cat for cat in event.categories if cat.name==mapping ][0]
                    target.results.append(result)
                    has_mapped = True
                    break
            if not has_mapped:
                # if we get here, the runner only ran md events, add to first category
                target = [cat for cat in event.categories if cat.name==possible_categories[0]][0]
                target.results.append(result)
                print "MD: unable to determine mapping for %s"%(result)

# Generate scores for events
for event in events:
    for category in event.categories:
        # warn if we drop a category
        if category.name not in categories:
            print "%s: dropping category %s"%(event.name, category.name)
            continue
        # select the correct points to give to runners
        if not event.is_last:
            points_range = points
        else:
            points_range = lastpoints
        # Assign points
        def ressort(result):
            return result.time
        results = sorted(category.results, key=ressort)
        for (result,score) in zip(results, points_range):
            result.score = score
        # postprocessing
        prev_time = 0
        prev_score = 0
        for result in results:
            # handle ex-aequo's
            if result.time == prev_time:
                result.score = prev_score
            # default scores
            if result.score is None:
                result.score = 1
            prev_time = result.time
            prev_score = result.score
    # output the event
    main = Template(filename="templates/results.html")
    f = open("output/%s.html"%(event.name),"w")
    f.write(main.render_unicode(event=event).encode("utf-8"))
    f.close()

# Generate a ranking
non_ranked = [] # keep track of all clubs that shouldn't be ranked
for category in categories:
    def sf(runner):
        return runner.total
    runners = {}
    
    # Get the results for this category for any event
    races = []
    for event in events:
        for cat in event.categories:
            if cat.name == category:
                races.append(cat)
    for race in races:
        for result in race.results:
            # a runner can appear for multiple clubs, 
            # only results for Belgian clubs are accepted.
            if result.club not in club_whitelist:
                if result.club not in non_ranked:
                    non_ranked.append(result.club)
                continue
            if result.name not in runners:
                runners[result.name] = Runner()
                runners[result.name].name = result.name
                runners[result.name].club = result.club
            runners[result.name].results.append(result.score)
    # Compute the total
    for runner in runners:
        runners[runner].total = sum(sorted(runners[runner].results, reverse=True)[0:max_count])
    # Compute the place
    place= 1
    prev_score = 0
    prev_place = 0
    for runner in sorted(runners.values(), key=sf, reverse=True):
        if runner.total == prev_score:
            runner.place = prev_place
        else:
            runner.place = place
            prev_place = place
        prev_score = runner.total
        place = place + 1
    # produce the output
    for runner in runners.values():
        for competition in competitions:
            # find competition results for this runner
            date = competition[0:8]
            event = [ event for event in events if event.name==date ][0]
            cat = [ cat for cat in event.categories if cat.name==category ]
            if len(cat) > 0:
                has_run = False
                for result in cat[0].results:
                    if result.name==runner.name and result.club==runner.club:
                        runner.data.append(result.score)
                        has_run = True
                if not has_run:
                    runner.data.append(0)
    template = Template(filename="templates/ranking.html")
    f = open("output/%s.html"%(category),"w")
    f.write(template.render_unicode(categories=categories, category=category, runners=sorted(runners.values(),key=sf,reverse=True)).encode("utf-8"))
    f.close()
print "These clubs appear but aren't taken into account for the ranking:"
print non_ranked
