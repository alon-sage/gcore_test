#!/usr/bin/env bash

set -e

./manage.py check --deploy

exec "$@"