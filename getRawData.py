import functools
import json
import os
from datetime import datetime, timedelta
from ossapi import Ossapi, GameMode
from ossapi.enums import RankStatus, BeatmapsetSearchSort, BeatmapsetSearchExplicitContent

import ossapiKey

api = Ossapi(ossapiKey.client_id, ossapiKey.client_secret)


def generate_time_query(start_date, end_date):
    result = []
    current_date = start_date
    while True:
        result.append(f'ranked={current_date.year}.{current_date.month}.{current_date.day}')
        current_date = current_date + timedelta(days=1)
        if current_date > end_date:
            break
    return result


class User:
    def __init__(self, user_id,
                 username,
                 country,
                 previous_usernames):
        self.user_id = user_id
        self.username = username
        self.country = country
        self.previous_usernames = previous_usernames


class Beatmap:
    def __init__(self,
                 mode,
                 map_id,
                 cs,
                 diff_name,
                 diff_owners,
                 star_rating,
                 drain_time,
                 pass_count,
                 play_count):
        self.mode = mode
        self.map_id = map_id
        self.key = cs if self.mode == 3 else 0
        self.diff_name = diff_name
        self.diff_owners = diff_owners
        self.star_rating = star_rating
        self.drain_time = drain_time
        self.pass_count = pass_count
        self.play_count = play_count


class Beatmapset:
    def __init__(self,
                 set_id,
                 host,
                 artist,
                 title,
                 bn,
                 beatmaps,
                 ranked_date,
                 status,
                 vote_count,
                 rating):
        self.set_id = set_id
        self.host = host
        self.artist = artist
        self.title = title
        self.bn = bn
        self.beatmaps = beatmaps
        self.ranked_date = ranked_date
        self.status = status
        self.vote_count = vote_count
        self.rating = rating


def sort_diff(self, other):
    if self.key > other.key:
        return 1
    if self.key == other.key:
        if self.star_rating > other.star_rating:
            return 1
        elif self.star_rating == other.star_rating:
            return 0
        return -1
    return -1


def search_beatmap(set_id) -> Beatmapset:
    _set = api.beatmapset(beatmapset_id=set_id)
    host = _set.user_id
    _bn = []
    _maps = []
    for i in _set.current_nominations:
        _bn.append(i.user_id)
    for i in _set.beatmaps:
        _m = {GameMode.OSU: 0,
              GameMode.TAIKO: 1,
              GameMode.CATCH: 2,
              GameMode.MANIA: 3}
        _maps.append(Beatmap(
            _m[i.mode],
            i.id,
            round(i.cs),
            i.version,
            [x.id for x in i.owners],
            i.difficulty_rating,
            i.hit_length,
            i.passcount,
            i.playcount
        ))
    # _beatmap = sorted(_beatmap, key=lambda i: i.star_rating)
    _beatmap = sorted(_maps, key=functools.cmp_to_key(sort_diff))
    vote_count = sum(_set.ratings)
    _ratings = 0
    for i in range(11):
        _ratings += i * _set.ratings[i]
    result = Beatmapset(_set.id,
                        host,
                        _set.artist_unicode,
                        _set.title_unicode,
                        _bn,
                        _beatmap,
                        _set.ranked_date,
                        'ranked' if _set.ranked == RankStatus.RANKED else 'loved',
                        vote_count,
                        0 if vote_count == 0 else round(_ratings / vote_count * 100) / 100)
    return result


def save_beatmap_result(beatmapsets_data):
    result = []
    for i in beatmapsets_data:
        _beatmaps = []
        for _ in i.beatmaps:
            _beatmaps.append(Beatmap(
                _.mode,
                _.map_id,
                _.key,
                _.diff_name,
                _.diff_owners,
                _.star_rating,
                _.drain_time,
                _.pass_count,
                _.play_count
            ))
        result.append(Beatmapset(
            i.set_id,
            i.host,
            i.artist,
            i.title,
            i.bn,
            [_.__dict__ for _ in _beatmaps],
            str(i.ranked_date).split('+')[0],
            i.status,
            i.vote_count,
            i.rating
        ).__dict__)
    json.dump(result, open(f'rawData/{result[0]['ranked_date'].split(' ')[0].replace('-', '')}.json', 'w'),
              indent=4)


users = []
user_list = []


def load_user_data():
    if not os.path.exists('user.json'):
        with open('user.json', 'w+') as f:
            f.write('[]')
    with open('user.json', 'r') as f:
        data = json.load(f)
    for user in data:
        users.append(User(user["user_id"],
                          user["username"],
                          user["country"],
                          user["previous_usernames"]))
        user_list.append(user["user_id"])


def get_user_info(user_id: int) -> User:
    try:
        user_info = api.user(user_id)
        return User(user_id, user_info.username, user_info.country.name, user_info.previous_usernames)
    except:
        return User(user_id, f'ERROR_{user_id}', '', [])


def refresh_user_data():
    index = 0
    beatmap_data = os.listdir('rawData')
    print(beatmap_data)
    for i in beatmap_data:
        with open(f"rawData/{i}") as f:
            data = json.load(f)
            for mapset in data:
                if mapset["host"] not in user_list:
                    users.append(get_user_info(mapset["host"]))
                    user_list.append(mapset["host"])
                    index += 1
                    print(users[-1].__dict__)
                else:
                    print(f"Host ID {mapset['host']} Already Exists")
                for bn in mapset["bn"]:
                    if bn not in user_list:
                        users.append(get_user_info(bn))
                        user_list.append(bn)
                        index += 1
                        print(users[-1].__dict__)
                    else:
                        print(f"BN ID {bn} Already Exists")
                for diff in mapset["beatmaps"]:
                    for owner in diff["diff_owners"]:
                        if owner not in user_list:
                            users.append(get_user_info(owner))
                            user_list.append(owner)
                            index += 1
                            print(users[-1].__dict__)
                        else:
                            print(f"Mapper ID {owner} Already Exists")
        if index > 49:
            index -= 50
            with open("user.json", "w") as f:
                json.dump([user.__dict__ for user in users], f, indent=4)
    with open("user.json", "w") as f:
        json.dump([user.__dict__ for user in users], f, indent=4)


def get_beatmap_info(st, et):
    req_queue = generate_time_query(st, et)
    for q in req_queue:
        search_result = api.search_beatmapsets(query=q,
                                               sort=BeatmapsetSearchSort.RANKED_ASCENDING,
                                               explicit_content=BeatmapsetSearchExplicitContent.SHOW).beatmapsets
        print(q)
        _ = []
        for beatmapset in search_result:
            print(beatmapset.id)
            _.append(search_beatmap(beatmapset.id))
        save_beatmap_result(_)


def refresh_user_info():
    load_user_data()
    refresh_user_data()


if __name__ == "__main__":
    start_time = (
        datetime(2024, 11, 1))
    end_time = (
        datetime(2024, 12, 31))

    getBeatmapInfo = False
    getUserInfo = True

    if getBeatmapInfo:
        get_beatmap_info(start_time, end_time)

    if getUserInfo:
        refresh_user_info()
