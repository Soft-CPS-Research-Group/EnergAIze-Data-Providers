from apscheduler.schedulers.background import BlockingScheduler
import time

def job():
    print(f"Job executed at {time.ctime()}")

scheduler = BlockingScheduler()
scheduler.add_job(job, 'interval', minutes=1)
scheduler.start()

try:
    while True:
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
