FROM postgres:14-alpine

CMD ["bash", "-c", "\
    until pg_basebackup --pgdata=/var/lib/postgresql/data -R --slot=replication_slot --host=db --port=5432; do \
    echo 'Waiting for primary to connect...'; \
    sleep 1s; \
    done; \
    echo 'Backup done, starting replica...'; \
    chmod 0700 /var/lib/postgresql/data; \
    postgres"]
