import asyncio
import time

from modules.keyboard import *
from modules.database import *


async def main():
    try:
        time_start = time.time()
        markup = await Pars(4, '1020238041', 1687750200, 1687761600)
        print(time.time() - time_start)
    except Exception as e:
        print(e)

if __name__ == '__main__':
    asyncio.run(main())
