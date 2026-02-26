import asyncio
import itertools

async def spin(msg: str) -> None:
    for char in itertools.cycle(r'\|/-'):
        status = f'\r{char} {msg}'
        print(status, flush=True, end='')
        try:
            await asyncio.sleep(.1)
        except asyncio.CancelledError:
            break
    blanks = ' ' * len(status)
    print(f'\r{blanks}\r', end='')


async def slow() -> int:
    await asyncio.sleep(3)
    return 42
    
def main() -> None:
    result = asyncio.run(supervisor())
    print(f'Answer: {result}')

async def supervisor() -> int:
    spinner = asyncio.create_task(spin('thinking!'))
    print(f'spinner object: {spinner}')
    result = await slow()
    spinner.cancel()
    return result

if __name__ == '__main__':
    main()
    
-------------------------------------------------------------------------------------------------------------
#
# 🔹 Big Idea
#
# This program runs two coroutines concurrently:
#
# spin() → shows a rotating spinner in the terminal
#
# slow() → simulates a slow task (3 seconds)
#
# Both run on a single thread, using the asyncio event loop.
#
# No real parallelism. Just cooperative multitasking.
#
# 🔹 Execution Flow (Step-by-Step)
# 1️⃣ Program starts here
# if __name__ == '__main__':
#     main()
#
# So main() runs.
#
# 2️⃣ main() runs
# def main() -> None:
#     result = asyncio.run(supervisor())
#     print(f'Answer: {result}')
#
# asyncio.run(supervisor()):
#
# Creates an event loop
#
# Runs the coroutine supervisor()
#
# Closes the loop when done
#
# 3️⃣ supervisor() runs inside event loop
# async def supervisor() -> int:
#     spinner = asyncio.create_task(spin('thinking!'))
#     print(f'spinner object: {spinner}')
#     result = await slow()
#     spinner.cancel()
#     return result
#
# Let's break this carefully.
#
# 🔸 Line 1
# spinner = asyncio.create_task(spin('thinking!'))
#
# This:
#
# Wraps spin() in a Task
#
# Schedules it to run
#
# Returns immediately
#
# ⚠️ Important:
#
# spin() does NOT fully run here.
# It is just scheduled.
#
# Now we have TWO coroutines scheduled:
#
# supervisor
#
# spin
#
# 🔸 Next line
# result = await slow()
#
# Now supervisor() pauses here.
#
# When it hits await, control goes back to the event loop.
#
# The loop now says:
#
# "Okay, supervisor is waiting. What else can I run?"
#
# Answer: spin().
#
# 🔹 Now spin() starts running
# async def spin(msg: str) -> None:
#     for char in itertools.cycle(r'\|/-'):
#
# This cycles forever:
#
# \ | / - \ | / -
#
# Each loop:
#
# status = f'\r{char} {msg}'
# print(status, flush=True, end='')
# await asyncio.sleep(.1)
# 🔹 WHY is await asyncio.sleep(.1) needed?
#
# This is the most important part.
#
# Without it:
#
# spin() would run an infinite loop
#
# It would NEVER give control back to the event loop
#
# slow() would NEVER run
#
# Program would freeze
#
# What await asyncio.sleep(.1) actually does:
#
# Suspends spin() for 0.1 seconds
#
# Gives control back to event loop
#
# Event loop runs other tasks (like slow())
#
# This is called cooperative multitasking.
#
# Coroutines must voluntarily yield control.
#
# That's what await does.
#
# 🔹 Meanwhile: slow() runs
# async def slow() -> int:
#     await asyncio.sleep(3)
#     return 42
#
# This also yields control for 3 seconds.
#
# So the event loop keeps switching:
#
# spin → sleep(.1)
# slow → sleep(3)
# spin → sleep(.1)
# spin → sleep(.1)
# spin → sleep(.1)
# ...
#
# For 3 seconds, spinner keeps printing.
#
# 🔹 After 3 seconds
#
# slow() finishes and returns 42.
#
# So now inside supervisor():
#
# result = await slow()
#
# gets 42.
#
# 🔹 Then this runs:
# spinner.cancel()
#
# This sends a cancellation request to the spin task.
#
# 🔹 What happens inside spin()?
#
# When a task is cancelled:
#
# The next await raises asyncio.CancelledError
#
# Your code handles that:
#
# try:
#     await asyncio.sleep(.1)
# except asyncio.CancelledError:
#     break
#
# So:
#
# The exception is caught
#
# Loop breaks
#
# Spinner exits cleanly
#
# Then it clears the spinner line:
#
# blanks = ' ' * len(status)
# print(f'\r{blanks}\r', end='')
# 🔹 Final Flow Summary
# main()
#   ↓
# asyncio.run(supervisor())
#   ↓
# create_task(spin)
#   ↓
# await slow()
#         ↓
#     spin runs repeatedly
#     sleep(.1) yields control
#         ↓
#     slow finishes after 3 sec
#   ↓
# spinner.cancel()
#   ↓
# spin catches CancelledError
#   ↓
# clean exit
#   ↓
# return 42
#   ↓
# print Answer: 42