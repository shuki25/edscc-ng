from __future__ import absolute_import

import time

from celery.utils.log import get_task_logger
from celery.exceptions import SoftTimeLimitExceeded
from django.contrib.auth.models import User

from config import celery_app
from edscc.core.parser import ParseJournalLogFile
from edscc.core.session_tracker import SessionTrackerManager

log = get_task_logger(__name__)


@celery_app.task(name="edscc.commander.tasks.parse_journal_file", soft_time_limit=300)
def parse_journal_file(user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    session = SessionTrackerManager(
        user=user,
        session_identifier="upload",
        initial_payload={"celery_task": False},
    )

    print("in celery task: parse_journal_file(%s)" % user_id)
    log.debug("Starting parse_journal_file(%s) task" % user_id)
    try:
        session.set_attr("celery_task", True)
        parser = ParseJournalLogFile(user_id)
        num_remaining = parser.start(num_logs_process=25)
        if num_remaining:
            parse_journal_file.apply_async(args=[user_id], countdown=10)
        else:
            session.set_attr("celery_task", False)
    except SoftTimeLimitExceeded:
        log.warning("SoftTimeLimitExceeded")
        time.sleep(5)
        parse_journal_file.apply_async(args=[user_id], countdown=10)
