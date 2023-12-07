# -*- coding: utf8 -*-
import asyncio
import datetime

import aiofiles
import asyncpg
from transliterate import translit, get_available_language_codes

password = ''
host = ''
database = ''


async def connector():
    return await asyncpg.connect(user='postgres', password=password, database=database, host=host)


async def close(conn):
    await conn.close()


async def ERROR(conn, exception, name):
    await close(conn)
    print(f"{name}: {exception}")


async def DB_reg(user_id: str, username: str):
    conn = await connector()
    try:
        answer = await conn.fetchrow(""" 
            SELECT update_user($1, $2);
        """, str(user_id), str(username))
        await close(conn)
        return answer.get('update_user')
    except Exception as e:
        await ERROR(conn, e, 'DB_reg')
    finally:
        await close(conn)


async def DB_reg_pass(user_id: str):
    conn = await connector()
    try:
        await conn.fetchrow("""
            UPDATE public.users SET register=true WHERE user_id=$1;
        """, str(user_id))
    except Exception as e:
        await ERROR(conn, e, 'DB_reg_pass')
    finally:
        await close(conn)


async def Set_group(user_id: str, username: str, group: str):
    conn = await connector()
    try:
        a = await conn.fetchrow(""" 
            SELECT set_group($1, $2, $3);
            """, str(user_id), str(group), str(username))
        await close(conn)
        return a.get('set_group')
    except Exception as e:
        await ERROR(conn, e, 'Set_group')
    finally:
        await close(conn)


async def Set_pod_group(user_id: str, group_pod: str):
    conn = await connector()
    try:
        a = await conn.fetchrow(""" 
        UPDATE public.users SET group_pod=$2 WHERE user_id=$1;
        """, str(user_id), str(group_pod))
        await close(conn)
    except Exception as e:
        await ERROR(conn, e, 'Set_pod_group')
    finally:
        await close(conn)


# ____________________________________________ Get pars ________________________________________________________________
async def Pars(method: int, user_id: str, now_day=None, end_day=None, conn_start=None):
    if conn_start is None:
        conn = await connector()
    else:
        conn = conn_start
    info_user = await conn.fetchrow(""" SELECT * FROM public.users WHERE user_id=$1; """, str(user_id))
    if info_user is not None:
        group = info_user.get("group")
        if group is not None:
            weekday = datetime.datetime.now().weekday()
            if method == 1:
                now_day = datetime.datetime.strptime(str(datetime.datetime.now().date()), '%Y-%m-%d')
                end_day = (now_day + datetime.timedelta(days=1))
                now_day = (end_day - datetime.timedelta(days=1)).timestamp()
                end_day = end_day.timestamp()
            elif method == 2:
                now_day = datetime.datetime.strptime(str(datetime.datetime.now().date()), '%Y-%m-%d')
                end_day = (now_day + datetime.timedelta(days=2))
                now_day = (end_day - datetime.timedelta(days=1)).timestamp()
                end_day = end_day.timestamp()
            elif method == 3:
                now_day = datetime.datetime.strptime(str(datetime.datetime.now().date()), '%Y-%m-%d')
                now_day = (now_day - datetime.timedelta(days=weekday))
                end_day = (now_day + datetime.timedelta(days=7))
                end_day = end_day.timestamp()
                now_day = now_day.timestamp()
            elif method == 4:
                pass
            else:
                now_day = datetime.datetime.strptime(str(datetime.datetime.now().date()), '%Y-%m-%d')
                end_day = (now_day + datetime.timedelta(days=1)).timestamp()
                now_day = now_day.timestamp()
            if datetime.datetime.fromtimestamp(float(now_day)).weekday() == 6 or weekday == 6:
                if method != 3:
                    if conn_start is None:
                        await close(conn)
                    return [False, 'No pars to day']
                now_day = datetime.datetime.strptime(str(datetime.datetime.now().date()), '%Y-%m-%d')
                now_day = (now_day - datetime.timedelta(days=weekday) + datetime.timedelta(days=7))
                end_day = (now_day + datetime.timedelta(days=14))
                end_day = end_day.timestamp()
                now_day = now_day.timestamp()
            pars_data = await conn.fetch(""" 
    SELECT * FROM public.schedule WHERE group_name=$1 and $2::float <= start_time::float and start_time::float <= $3::float ORDER BY (start_time::float); 
            """, str(translit(group, 'ru')), float(now_day), float(end_day))
            if len(pars_data) == 0:
                if conn_start is None:
                    await close(conn)
                return [False, 'No pars']
            pod_gr = int(info_user.get('group_pod'))
            text = await conn.fetchrow(""" SELECT * FROM public.edit_text_data WHERE id=$1 """,
                                       int(info_user.get("used_text")))
            day_text = str(text.get("day"))
            pars_text = str(text.get("pars"))
            spliter_text = str(text.get("split"))
            output_data = []
            loop = 0
            day_temp = -1
            output_data_day = []
            main_loop = 1
            for pars in pars_data:
                day_temp1 = datetime.datetime.fromtimestamp(float(pars.get("start_time"))).weekday()
                start_time23 = pars.get("start_time")
                if day_temp1 == day_temp:
                    next_day = False
                else:
                    day_temp = day_temp1
                    next_day = True
                loop += 1
                number = loop
                if pod_gr == 0:
                    text = pars.get('subject_name')
                    cab = pars.get('classroom')
                    teacher = pars.get('teacher_name')
                elif pod_gr == 1:
                    text = pars.get('subject_name_1')
                    cab = pars.get('classroom_1')
                    teacher = pars.get('teacher_name_1')
                elif pod_gr == 2:
                    text = pars.get('subject_name_2')
                    cab = pars.get('classroom_2')
                    teacher = pars.get('teacher_name_2')
                else:
                    text = pars.get('subject_name')
                    cab = pars.get('classroom')
                    teacher = pars.get('teacher_name')
                start_time = f'{datetime.datetime.fromtimestamp(float(pars.get("start_time"))).strftime("%H:%M")}'
                end_time = f'{datetime.datetime.fromtimestamp(float(pars.get("end_time"))).strftime("%H:%M")}'
                if text != '' or cab != '' or teacher != '':
                    if next_day is False:
                        if len(output_data_day) != 0:
                            output_data_day.append(
                                pars_text.format(
                                    number=str(number),
                                    text=str(text),
                                    cab=str(cab),
                                    teacher=str(teacher),
                                    start_time=str(start_time),
                                    end_time=str(end_time)
                                )
                            )
                        else:
                            if day_temp1 == 0:
                                day_str = 'Понедельник'
                            elif day_temp1 == 1:
                                day_str = 'Вторник'
                            elif day_temp1 == 2:
                                day_str = 'Среда'
                            elif day_temp1 == 3:
                                day_str = 'Четверг'
                            elif day_temp1 == 4:
                                day_str = 'Пятница'
                            elif day_temp1 == 5:
                                day_str = 'Суббота'
                            elif day_temp1 == 6:
                                day_str = 'Воскресенье'
                            else:
                                day_str = ''
                            output_data_day.append(
                                day_text.format(day=str(day_str)) +
                                pars_text.format(
                                    number=str(number),
                                    text=str(text),
                                    cab=str(cab),
                                    teacher=str(teacher),
                                    start_time=str(start_time),
                                    end_time=str(end_time)
                                )
                            )
                    else:
                        temp = datetime.datetime.fromtimestamp(float(pars.get("start_time")))
                        now_day = datetime.datetime.strptime((temp - datetime.timedelta(days=1)).strftime("%d.%m.%Y"),
                                                             "%d.%m.%Y").timestamp()
                        end_day = datetime.datetime.strptime(temp.strftime("%d.%m.%Y"), "%d.%m.%Y").timestamp()
                        if main_loop == 0:
                            output_data.append(
                                [str(str(f'{spliter_text}'.join(output_data_day)) + spliter_text), int(now_day),
                                 int(end_day)])
                        else:
                            main_loop = 0
                        loop = 1
                        number = loop
                        output_data_day = []
                        if day_temp1 == 0:
                            day_str = 'Понедельник'
                        elif day_temp1 == 1:
                            day_str = 'Вторник'
                        elif day_temp1 == 2:
                            day_str = 'Среда'
                        elif day_temp1 == 3:
                            day_str = 'Четверг'
                        elif day_temp1 == 4:
                            day_str = 'Пятница'
                        elif day_temp1 == 5:
                            day_str = 'Суббота'
                        elif day_temp1 == 6:
                            day_str = 'Воскресенье'
                        else:
                            day_str = ''
                        output_data_day.append(
                            day_text.format(day=str(day_str)) +
                            pars_text.format(
                                number=str(number),
                                text=str(text),
                                cab=str(cab),
                                teacher=str(teacher),
                                start_time=str(start_time),
                                end_time=str(end_time)
                            )
                        )
                else:
                    if next_day is True:
                        temp = datetime.datetime.fromtimestamp(float(pars.get("start_time")))
                        now_day = datetime.datetime.strptime((temp - datetime.timedelta(days=1)).strftime("%d.%m.%Y"),
                                                             "%d.%m.%Y").timestamp()
                        end_day = datetime.datetime.strptime(temp.strftime("%d.%m.%Y"), "%d.%m.%Y").timestamp()
                        if main_loop == 0:
                            output_data.append(
                                [str(str(f'{spliter_text}'.join(output_data_day)) + spliter_text), int(now_day),
                                 int(end_day)])
                        else:
                            main_loop = 0
                        loop = 0
                        output_data_day = []
            temp = datetime.datetime.fromtimestamp(float(start_time23))
            end_day = datetime.datetime.strptime((temp + datetime.timedelta(days=1)).strftime("%d.%m.%Y"),
                                                 "%d.%m.%Y").timestamp()
            now_day = datetime.datetime.strptime(temp.strftime("%d.%m.%Y"), "%d.%m.%Y").timestamp()
            if main_loop == 0:
                output_data.append(
                    [str(str(f'{spliter_text}'.join(output_data_day)) + spliter_text), int(now_day),
                     int(end_day)])
            if conn_start is None:
                await close(conn)
            return [True, output_data]
        else:
            if conn_start is None:
                await close(conn)
            return [False, "No found group"]
    else:
        if conn_start is None:
            await close(conn)
        return [False, "No found user"]


async def Get_group_list():
    conn = await connector()
    try:
        data = await conn.fetch(""" 
            SELECT group_name FROM public.schedule
            Group BY group_name
            ORDER BY group_name ASC
        """)

        group_list = []
        for item in data:
            group_list.append(item.get("group_name"))
        await conn.close()
        return group_list
    except Exception as e:
        await ERROR(conn, 'Get_group_list', e)


# _________________________________________ Premium methods ____________________________________________________________
async def Auto_send():
    conn = await connector()
    try:
        users_data = await conn.fetch(""" 
            SELECT * FROM public.users WHERE auto_send='1'
        """)
        
        await conn.close()
    except Exception as e:
        await ERROR(conn, 'Auto_send', e)


if __name__ == '__main__':
    a = asyncio.run(Pars(1, '1020238041'))
    print(a)
