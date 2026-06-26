#!/bin/sh
set -eu

INTERVAL_SECONDS="${SCHEDULER_INTERVAL_SECONDS:-60}"

echo "Scheduler iniciado com intervalo de ${INTERVAL_SECONDS}s."

while true; do
  if ! python manage.py close_overdue_tickets; then
    echo "Falha ao executar o scheduler. Tentando novamente no proximo ciclo."
  fi
  sleep "${INTERVAL_SECONDS}"
done
