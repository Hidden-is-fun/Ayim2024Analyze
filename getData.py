"""
SQLite Ver.
"""
from ossapi import Ossapi, GameMode
from ossapi.enums import RankStatus, BeatmapsetSearchSort, BeatmapsetSearchExplicitContent
import ossapiKey
from datetime import datetime, timedelta
import sqlite3

api = Ossapi(ossapiKey.client_id, ossapiKey.client_secret)

conn = sqlite3.connect('statistics.db')
c = conn.cursor()


def generate_time_query(start_date, end_date):
    result = []
    current_date = start_date
    while True:
        result.append(f'ranked={current_date.year}.{current_date.month}.{current_date.day}')
        current_date = current_date + timedelta(days=1)
        if current_date > end_date:
            break
    return result


def search_and_insert_beatmap_info(set_id):
    _set = api.beatmapset(beatmapset_id=set_id)
    host = _set.user_id
    for i in _set.current_nominations:
        c.execute(f"""
        INSERT INTO BN (SetID, UserID) SELECT {set_id}, {i.user_id} 
        WHERE NOT EXISTS (SELECT * FROM BN WHERE SetID = {set_id} AND UserID = {i.user_id})
        """)
        conn.commit()

        user = conn.execute(f"SELECT * FROM User WHERE UserID = {i.user_id}")
        count = 0
        for row in user:
            count += 1
        if not count:
            try:
                user_info = api.user(i.user_id)
                c.execute(f"""
                            INSERT INTO User (UserID, Username, Country, UpdateTime) VALUES (
                            {i.user_id},
                            '{user_info.username}',
                            '{user_info.country.name.replace("\'", "\'\'")}',
                            DATETIME('NOW'))
                            """)
                conn.commit()

                for alias in user_info.previous_usernames:
                    c.execute(f"""
                    INSERT INTO UserAlias (UserID, PreviousUsername) VALUES (
                    {i.user_id}, '{alias}')
                    """)
                    conn.commit()
            except Exception as e:
                print(e)
                c.execute(f"""
                INSERT INTO User (UserID, Username, Country, UpdateTime) VALUES (
                {i.user_id}, NULL, NULL, DATETIME('NOW'))
                """)
                conn.commit()
            print(f' - Insert BN Info <{i.user_id}> Successfully')

    for i in _set.beatmaps:
        _m = {GameMode.OSU: 0,
              GameMode.TAIKO: 1,
              GameMode.CATCH: 2,
              GameMode.MANIA: 3}

        diff_name = i.version.replace("'", "''")
        c.execute(f"""
        INSERT INTO Beatmap (SetID, MapID, GameMode, KeyCount, DiffName, SR, Drain, PassCount, PlayCount, UpdateTime)
        SELECT 
        {_set.id},
        {i.id},
        {_m[i.mode]},
        {'NULL' if _m[i.mode] != 3 else round(i.cs)},
        '{diff_name}',
        {i.difficulty_rating},
        {i.hit_length},
        {i.passcount},
        {i.playcount},
        DATETIME('NOW')
        WHERE NOT EXISTS (SELECT * FROM Beatmap WHERE MapID = {i.id})
        """)
        conn.commit()

        for owner in i.owners:
            owner_id = owner.id
            c.execute(f"""
            INSERT INTO DiffOwner (MapID, UserID) SELECT {i.id}, {owner_id}
            WHERE NOT EXISTS (SELECT * FROM DiffOwner WHERE MapID = {i.id} and UserID = {owner_id})
            """)

            user = conn.execute(f"SELECT * FROM User WHERE UserID = {owner_id}")
            count = 0
            for row in user:
                count += 1
            if not count:
                try:
                    user_info = api.user(owner_id)
                    c.execute(f"""
                    INSERT INTO User (UserID, Username, Country, UpdateTime) VALUES (
                    {owner_id},
                    '{user_info.username}',
                    '{user_info.country.name.replace("\'", "\'\'")}',
                    DATETIME('NOW'))
                    """)
                    conn.commit()

                    for alias in user_info.previous_usernames:
                        c.execute(f"""
                        INSERT INTO UserAlias (UserID, PreviousUsername) VALUES (
                        {owner_id}, '{alias}')
                        """)
                        conn.commit()
                except Exception as e:
                    print(e)
                    c.execute(f"""
                    INSERT INTO User (UserID, Username, Country, UpdateTime) VALUES (
                    {owner_id}, NULL, NULL, DATETIME('NOW'))
                    """)
                    conn.commit()
                print(f' - Insert Mapper Info <{owner_id}> Successfully')

    vote_count = sum(_set.ratings)
    _ratings = 0
    for i in range(11):
        _ratings += i * _set.ratings[i]

    artist = _set.artist_unicode.replace("'", "''")
    title = _set.title_unicode.replace("'", "''")
    c.execute(f"""
    INSERT INTO BeatmapSet (SetID, Host, Artist, Title, Diffs, RankedDate, IsRanked, VoteCount, Rating)
    SELECT 
    {_set.id},
    {host},
    '{artist}',
    '{title}',
    {len(_set.beatmaps)},
    '{_set.ranked_date}',
    {'TRUE' if _set.ranked == RankStatus.RANKED else 'FALSE'},
    {vote_count},
    {0 if vote_count == 0 else round(_ratings / vote_count * 100) / 100}
    WHERE NOT EXISTS (SELECT * FROM BeatmapSet WHERE SetID = {_set.id})
    """)
    conn.commit()
    print(f"Insert BeatmapSet Info <{set_id}> Successfully")


def update_data(st, et):
    req_queue = generate_time_query(st, et)
    for q in req_queue:
        search_result = api.search_beatmapsets(query=q,
                                               sort=BeatmapsetSearchSort.RANKED_ASCENDING,
                                               explicit_content=BeatmapsetSearchExplicitContent.SHOW).beatmapsets
        print(q)
        for beatmapset in search_result:
            search_and_insert_beatmap_info(beatmapset.id)


if __name__ == "__main__":
    start_time = (
        datetime(2024, 3, 20))
    end_time = (
        datetime(2025, 2, 10))
    update_data(start_time, end_time)

    conn.close()
