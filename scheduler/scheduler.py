from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

scheduler.start()


def add_job(run_time, func, topic, job_id=None, creds=None):

    scheduler.add_job(
        func,
        trigger="date",
        run_date=run_time,
        args=[topic, creds],
        id=job_id
    )


def remove_job(job_id):

    try:
        scheduler.remove_job(job_id)
    except Exception as e:
        print(f"Could not remove job {job_id} from memory (it may have already run): {e}")