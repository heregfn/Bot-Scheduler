# -*- coding: utf8 -*-
import json as js
import random
import time

import aiohttp
import asyncio
import pandas
import datetime
import aiofiles
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import asyncpg
import random
import re

password = ''
host = ''
database = 'YRTK'


async def connector():
    return await asyncpg.connect(user='postgres', password=password, database=database, host=host)


async def Get_Google(session: aiohttp.ClientSession, url: str, loop: int):
    async with session.get(url) as response:
        excel = f'excel/{loop}.xlsx'
        async with aiofiles.open(excel, 'wb') as file:
            data = await response.content.read()
            await file.write(data)
    pd = pandas.read_excel(str(excel), engine='openpyxl')
    cvs = pd.to_csv(encoding="utf-8", lineterminator='1312dfsfgra', quotechar="'", sep='*')
    cvs = cvs.replace("'", "")
    data = []
    string = []
    for item in cvs.split('*'):
        if '1312dfsfgra' in item:
            string.append(item.split('1312dfsfgra')[0])
            data.append(string)
            string = [item.split('1312dfsfgra')[1]]
            continue
        string.append(item)
    data = data[4:]
    groups = data[0]
    passed = False
    group_list = []
    len_group = 0
    for item in groups:
        if passed:
            if item is not None and item != '' and len(item) != 0:
                len_group += 5
                group_list.append([[item]])
        if 'Группа' in item:
            passed = True
    clear = []
    string = []
    day = []
    loop = 0
    for item in data[2:]:
        if item[1] is not None and item[1] != '':
            clear.append(day)
            day = []
        if loop == 1:
            string.append(item)
            day.append(string)
            string = []
            loop = 0
            continue
        string.append(item)
        loop += 1
    clear.append(day)

    for day in clear[1:]:
        daytime = day[0][0][1].split(' ')[0]
        groups_len_main = len(group_list) - 1
        for item in day:
            temp1 = len(item[0]) - 4
            loop = groups_len_main + 1
            for i in group_list:
                loop -= 1
                try:
                    group_list[loop] += [[[int(float(datetime.datetime.strptime(f'{daytime} {str(item[0][4].split("-")[0]).strip()}',
                                                                                '%d.%m.%Y %H:%M').timestamp())),
                                           int(float(datetime.datetime.strptime(f'{daytime} {str(item[0][4].split("-")[1]).strip()}',
                                                                                '%d.%m.%Y %H:%M').timestamp()))],
                                          item[0][temp1:][:4], item[1][temp1:][:4]]]
                except Exception as e:
                    print(f'{e}\n{item[0]}\n{item[1]}\n{url}\n')
                temp1 -= 5
    clear_group_list = []
    for group in group_list:
        name = group[0][0].strip().lower()
        for item in group[1:]:
            text = ''
            text_1 = ''
            text_2 = ''

            teacher = ''
            teacher_1 = ''
            teacher_2 = ''

            classroom = ''
            classroom_1 = ''
            classroom_2 = ''
            if item[1][0] != '' and item[1][1] != '' and item[1][2] != '' and item[1][3] != '':
                text += f'{item[1][0]} (Группа 1) и {item[1][2]} (Группа 2)'
                text_1 += f'{item[1][0]}'
                text_2 += f'{item[1][2]}'

                teacher += f'{item[2][0]} (Группа 1) и {item[2][3]} (Группа 2)'
                teacher_1 += f'{item[2][0]}'
                teacher_2 += f'{item[2][3]}'

                classroom += f'{str(item[1][1]).replace(".0", "")} (Группа 1) и {str(item[1][3]).replace(".0", "")} (Группа 2)'
                classroom_1 += f'{str(item[1][1]).replace(".0", "")}'
                classroom_2 += f'{str(item[1][3]).replace(".0", "")}'
                print(item, name)
            elif item[1][0] == '' and item[1][1] == '' and item[1][2] != '' and item[1][3] != '':
                text += f'{item[1][2]} (Группа 2)'
                text_2 += f'{item[1][2]}'

                teacher += f'{item[2][3]} (Группа 2)'
                teacher_2 += f'{item[2][3]}'

                classroom += f'{str(item[1][3]).replace(".0", "")} (Группа 2)'
                classroom_2 += f'{str(item[1][3]).replace(".0", "")}'
            elif item[1][0] != '' and item[1][1] != '' and item[1][2] == '' and item[1][3] == '':
                text += f'{item[1][0]} (Группа 1)'
                text_1 += f'{item[1][0]}'

                teacher += f'{item[2][0]} (Группа 1)'
                teacher_1 += f'{item[2][0]}'

                classroom += f'{str(item[1][1]).replace(".0", "")} (Группа 1)'
                classroom_1 += f'{str(item[1][1]).replace(".0", "")}'
            elif item[1][0] != '' and item[1][1] == '' and item[1][2] == '' and item[1][3] != '':
                text += f'{item[1][0]}'
                text_1 += f'{item[1][0]}'
                text_2 += f'{item[1][0]}'

                teacher += f'{item[2][0]}'
                teacher_1 += f'{item[2][0]}'
                teacher_2 += f'{item[2][0]}'

                classroom += f'{str(item[1][3]).replace(".0", "")}'
                classroom_1 += f'{str(item[1][3]).replace(".0", "")}'
                classroom_2 += f'{str(item[1][3]).replace(".0", "")}'
            clear_group_list.append([
                str(re.sub(r"""^"|"$|^'|'$|^\n|\n$""", '', name)),
                str(re.sub(r"""^"|"$|^'|'$|^\n|\n$""", '', text)),
                str(re.sub(r"""^"|"$|^'|'$|^\n|\n$""", '', text_1)),
                str(re.sub(r"""^"|"$|^'|'$|^\n|\n$""", '', text_2)),
                str(re.sub(r"""^"|"$|^'|'$|^\n|\n$""", '', teacher)),
                str(re.sub(r"""^"|"$|^'|'$|^\n|\n$""", '', teacher_1)),
                str(re.sub(r"""^"|"$|^'|'$|^\n|\n$""", '', teacher_2)),
                str(re.sub(r"""^"|"$|^'|'$|^\n|\n$""", '', classroom)),
                str(re.sub(r"""^"|"$|^'|'$|^\n|\n$""", '', classroom_1)),
                str(re.sub(r"""^"|"$|^'|'$|^\n|\n$""", '', classroom_2)),
                str(re.sub(r"""^"|"$|^'|'$|^\n|\n$""", '', str(item[0][0]))),
                str(re.sub(r"""^"|"$|^'|'$|^\n|\n$""", '', str(item[0][1]))),
                f'{name}_{str(item[0][0])}_{str(item[0][1])}'
            ])
    return clear_group_list


async def main():
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'user_agent': UserAgent()['google_chrome']
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        response = await session.get(url='https://urtt.ru/students/dnevnoe/raspisaniya/')
        content = await response.text()
        soup = BeautifulSoup(content.encode('utf-8'), 'html.parser')
        urls = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'https://docs.google.com/spreadsheets/d/' in href:
                href = str(href).split('https://docs.google.com/spreadsheets/d/')[1].split('/')[0]
                href = f'https://docs.google.com/spreadsheets/u/1/d/{href}/export/edit?format=xlsx'
                urls.append(href)
        urls = urls[:len(urls) - 1]
        tasks = []
        loop = 1

        for url in urls:
            task = asyncio.create_task(Get_Google(session, url, loop))
            loop += 1
            tasks.append(task)
        answers = await asyncio.gather(*tasks)
        # print(answers)
        conn = await connector()
        try:
            for clear_group_list in answers:
                await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.schedule_temp
            (
                group_name text COLLATE pg_catalog."default",
                subject_name text COLLATE pg_catalog."default",
                subject_name_1 text COLLATE pg_catalog."default",
                subject_name_2 text COLLATE pg_catalog."default",
                teacher_name text COLLATE pg_catalog."default",
                teacher_name_1 text COLLATE pg_catalog."default",
                teacher_name_2 text COLLATE pg_catalog."default",
                classroom text COLLATE pg_catalog."default",
                classroom_1 text COLLATE pg_catalog."default",
                classroom_2 text COLLATE pg_catalog."default",
                start_time text COLLATE pg_catalog."default",
                end_time text COLLATE pg_catalog."default",
                id_shelude text COLLATE pg_catalog."default" NOT NULL,
                CONSTRAINT schedule_temp_pkey PRIMARY KEY (id_shelude)
            )
    
            TABLESPACE pg_default;
    
            ALTER TABLE IF EXISTS public.schedule_temp
                OWNER to postgres;
            DELETE FROM public.schedule_temp;
                """)
                await conn.executemany(
                    """
    INSERT INTO schedule_temp 
        (group_name, subject_name, subject_name_1, subject_name_2, teacher_name, teacher_name_1, teacher_name_2, classroom, classroom_1, classroom_2, start_time, end_time, id_shelude)
    VALUES 
        ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13) ON CONFLICT (id_shelude) DO UPDATE
    SET group_name=$1, subject_name=$2, subject_name_1=$3, subject_name_2=$4, teacher_name=$5, teacher_name_1=$6, teacher_name_2=$7, classroom=$8, classroom_1=$9, classroom_2=$10, start_time=$11,
    end_time=$12""", clear_group_list)
                await conn.execute("""
            INSERT INTO public.schedule (group_name, subject_name, subject_name_1, subject_name_2, teacher_name, teacher_name_1, teacher_name_2, classroom, classroom_1, classroom_2, start_time, end_time, id_shelude)
            SELECT
                st.group_name,
                st.subject_name,
                st.subject_name_1,
                st.subject_name_2,
                st.teacher_name,
                st.teacher_name_1,
                st.teacher_name_2,
                st.classroom,
                st.classroom_1,
                st.classroom_2,
                st.start_time,
                st.end_time,
                st.id_shelude
            FROM public.schedule_temp st
            ON CONFLICT (id_shelude) DO UPDATE
            SET
                group_name = EXCLUDED.group_name,
                subject_name = EXCLUDED.subject_name,
                subject_name_1 = EXCLUDED.subject_name_1,
                subject_name_2 = EXCLUDED.subject_name_2,
                teacher_name = EXCLUDED.teacher_name,
                teacher_name_1 = EXCLUDED.teacher_name_1,
                teacher_name_2 = EXCLUDED.teacher_name_2,
                classroom = EXCLUDED.classroom,
                classroom_1 = EXCLUDED.classroom_1,
                classroom_2 = EXCLUDED.classroom_2,
                start_time = EXCLUDED.start_time,
                end_time = EXCLUDED.end_time;          
            DELETE FROM public.schedule_temp;
            """)
        finally:
            await conn.close()


if __name__ == '__main__':
    while True:
        try:
            asyncio.get_event_loop().run_until_complete(main())
            time.sleep(200)
        except Exception as e:
            pass
