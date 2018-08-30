# coding: utf8

import os
import json
import pprint
import taskcluster

event = json.loads(environ["GITHUB_EVENT"])
print("GitHub event:")
pprint.pprint(event)
print("")

task_id = taskcluster.slugId()
payload = {
    "taskGroupId": os.environ["DECISION_TASK_ID"],
    "dependencies": [os.environ["DECISION_TASK_ID"]],
    "schedulerId": "taskcluster-github",  # FIXME: can we avoid hard-coding this?
    "provisionerId": "aws-provisioner-v1",
    "workerType": "github-worker",
    "created": taskcluster.fromNowJSON(""),
    "deadline": taskcluster.fromNowJSON("1 hour"),
    "metadata": {
        "name": "Taskcluster experiments for Servo: Child task",
        "description": "",
        "owner": event["pusher"]["name"] + "@users.noreply.github.com",
        "source": event["compare"],
    },
    "payload": {
        "maxRunTime": 600,
        "image": "buildpack-deps:bionic",
        "command": [
            "/bin/bash",
            "--login",
            "-c",
            """
                git clone {event[repository][clone_url]} repo &&
                cd repo &&
                git checkout {event[after]} &&
                ./child-task.sh
            """.format(event=event),
        ],
        "artifacts": {
            "public/executable.gz": {
                "type": "file",
                "path": "/repo/something-rust/something-rust.gz",
                "expires": taskcluster.fromNowJSON("1 week"),
            },
        },
    },
}
# https://docs.taskcluster.net/docs/reference/workers/docker-worker/docs/features#feature-taskclusterproxy
queue = taskcluster.Queue(options={"baseUrl": "http://taskcluster/queue/v1/"})
queue.createTask(task_id, payload)
print("new task scheduled: " % task_id)
