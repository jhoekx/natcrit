#!/usr/bin/python3

import argparse
import datetime
import json
import xml.etree.ElementTree as ET

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import jinja2

NORMAL_SCORE = [30, 27, 25, 23, 21, 19, 17, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
EXTRA_SCORE = [45, 40, 37, 35, 32, 29, 26, 23, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]

RANKING_CATEGORIES = ['D-10', 'D-12', 'D-14', 'D-16', 'D-18', 'D-20', 'DE', 'D21', 'DB', 'D35', 'D40', 'D45', 'D50', 'D55', 'D60', 'D65', 'D70', 'D75', 'D80', 'D85', 'H-10', 'H-12', 'H-14', 'H-16', 'H-18', 'H-20', 'HE', 'H21', 'HB', 'H35', 'H40', 'H45', 'H50', 'H55', 'H60', 'H65', 'H70', 'H75', 'H80', 'H85']

RANKING_CLUBS = {
    'Altaïr C.O.': 'Altaïr C.O.',
    'ASUB': 'ASUB',
    'Balise 10': 'Balise 10',
    'Borasca': 'Borasca',
    'C.O. Liège': 'C.O. Liège',
    'C.O. Pégase': 'C.O. Pégase',
    'C.O.M.B': 'C.O.M.B',
    'C.O. Militaire Belge': 'C.O.M.B.',
    'hamok': 'hamok',
    'Hainaut O.C.': 'Hainaut O.C.',
    'Hermathenae': 'Hermathenae',
    'K.O.L.': 'K.O.L.',
    'N.S.V. Amel': 'N.S.V. Amel',
    'O.L.G. St. Vith "ARDOC"': 'O.L.G. St. Vith ARDOC',
    'O.L.G. St. Vith ARDOC': 'O.L.G. St. Vith ARDOC',
    'O.L.V. Eifel': 'O.L.V. Eifel',
    'O.L.V.E.': 'O.L.V. Eifel',
    'Omega': 'Omega',
    'Pégase': 'C.O. Pégase',
    'SUD O LUX': 'SUD O LUX',
    'TROL': 'TROL',
}

@dataclass
class Runner:
    name: str
    club: str
    scores: List[int]
    total: int = 0
    place: int = 0


@dataclass
class Result:
    position: int
    name: str
    club: str
    time: datetime.time
    status: str
    score: int = 0

    def is_ok(self) -> bool:
        return self.status == 'OK' and self.position != 0


@dataclass
class Category:
    name: str
    results: List[Result]

    def find_score(self, runner: Runner) -> int:
        for result in self.results:
            if result.name == runner.name and result.club == runner.club:
                return result.score
        return 0


@dataclass
class Event:
    date: str
    name: str
    location: str
    categories: List[Category]
    is_last: bool = False

    def find_category(self, name: str) -> Category:
        for category in self.categories:
            if category.name == name:
                return category
        return Category(name, [])


def result_from_data(data) -> Result:
    position = int(data['position'])
    name = data['name']
    club = data['club']
    time = datetime.time.fromisoformat(data['time'])
    status = data['status']
    return Result(position, name, club, time, status)


def category_from_data(data) -> Category:
    results = [result_from_data(result) for result in data['results']]
    return Category(data['name'], results)


def event_from_data(data, config) -> Event:
    categories = [category_from_data(v) for v in data['categories'].values()]
    event = Event(config['date'], config['name'], config['location'], categories)
    if 'is_last' in config and config['is_last'] is True:
        event.is_last = True
    return event


def read_event(event):
    date = event['date'].replace('-', '')
    with open(f'data/{date}.json') as f:
        return json.load(f)


def assign_scores(category: Category, scoring: List[int]):
    previous_time = None
    previous_score = None
    ok_results = [result for result in category.results if result.is_ok()]
    for i, result in enumerate(sorted(ok_results, key=lambda r: r.time)):
        if result.status != 'OK':
            continue
        if i > len(scoring) - 1:
            result.score = scoring[-1]
            continue
        if previous_time is not None and previous_time == result.time:
            result.score = previous_score
            continue
        previous_score = scoring[i]
        previous_time = result.time
        result.score = previous_score


def map_clubs(club_mapping: Dict[str, str], events: List[Event]) -> List[str]:
    unknown_clubs: List[str] = []
    for event in events:
        for category in event.categories:
            for result in category.results:
                if result.club in club_mapping:
                    result.club = club_mapping[result.club]
                else:
                    if result.club not in unknown_clubs:
                        unknown_clubs.append(result.club)
    return sorted(unknown_clubs)


def find_runners_in_category(category_name: str, events: List[Event], clubs: Dict[str, str]) -> List[Runner]:
    runners: Dict[str, Runner] = {}
    for event in events:
        category = event.find_category(category_name)
        for result in category.results:
            if result.club not in clubs:
                continue
            if result.name in runners:
                continue
            runners[result.name] = Runner(result.name, result.club, [])
    return [runner for runner in runners.values()]


def calculate_ranking(category_name: str, max_scores: int, runners: List[Runner], events: List[Event]):
    for runner in runners:
        for event in events:
            category = event.find_category(category_name)
            runner.scores.append(category.find_score(runner))

        runner.total = sum(sorted(runner.scores, reverse=True)[0:max_scores])

    previous_total = 0
    previous_place = 0
    for i, runner in enumerate(sorted(runners, key=lambda r: r.total, reverse=True), 1):
        if previous_place != 0 and runner.total == previous_total:
            runner.place = previous_place
            continue
        runner.place = i
        previous_total = runner.total
        previous_place = runner.place


def generate_xml(output_dir: Path, year: int, events: List[Event]):
    ranking = ET.Element('ranking')
    for event in events:
        e = ET.SubElement(ranking, 'event')
        ET.SubElement(e, 'name').text = event.name
        ET.SubElement(e, 'date').text = f': {event.date}'
        ET.SubElement(e, 'location').text = event.location
    ET.ElementTree(ranking).write(output_dir / f'N{year}.xml')


def print_events(events: List[Event]):
    for event in events:
        for category in event.categories:
            print(f'### {category.name} ###')
            for result in category.results:
                print(f'{result.time} {result.score} {result.name}')
            print('')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate Ranking')
    parser.add_argument('--config', required=True, dest='config', type=argparse.FileType())

    args = parser.parse_args()
    config = json.load(args.config)

    year = config['year']
    event_count = config['event_count']
    is_final = True if 'is_final' in config and config['is_final'] is True else False

    events = [event_from_data(read_event(event), event) for event in config['events']]

    for event in events:
        for category in event.categories:
            if event.is_last:
                assign_scores(category, EXTRA_SCORE)
            else:
                assign_scores(category, NORMAL_SCORE)

    unknown_clubs = map_clubs(RANKING_CLUBS, events)
    if len(unknown_clubs) > 0:
        print('These unknown clubs appear in the results:')
        for club in unknown_clubs:
            print(f'  {club}')

    jinja_env = jinja2.Environment(
        loader=jinja2.PackageLoader('natcrit3', 'templates'),
        autoescape=jinja2.select_autoescape(['html', 'xml'])
    )
    ranking_template = jinja_env.get_template('ranking.j2.html')

    output_dir = Path('output')
    year_dir = output_dir / f'N{year}'
    year_dir.mkdir(exist_ok=True)

    generate_xml(output_dir, year, events)

    with (output_dir / f'N{year}.htm').open(mode='w') as out:
        out.write(jinja_env.get_template('year.j2.html').render(
            year=year,
            categories=RANKING_CATEGORIES,
            today=datetime.date.today(),
            is_final=is_final,
            event_count=event_count,
            events=events,
        ))

    for category_name in RANKING_CATEGORIES:
        runners = find_runners_in_category(category_name, events, RANKING_CLUBS)
        calculate_ranking(category_name, event_count, runners, events)

        with (year_dir / f'{category_name}.html').open(mode='w') as out:
            out.write(ranking_template.render(
                year=year,
                categories=RANKING_CATEGORIES,
                event_count=event_count,
                category_name=category_name,
                runners=sorted(runners, key=lambda r: r.total, reverse=True)
            ))
