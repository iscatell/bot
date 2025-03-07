FROM postgres:14-alpine


ARG DB_REPL_PASSWORD
ARG DB_REPL_USER
ARG DB_USER
ARG DB_PASSWORD
ARG DB_DATABASE


RUN echo "CREATE USER ${DB_REPL_USER} REPLICATION ENCRYPTED PASSWORD '${DB_REPL_PASSWORD}';" > /docker-entrypoint-initdb.d/00_init.sql
RUN echo "SELECT pg_create_physical_replication_slot('replication_slot');" > /docker-entrypoint-initdb.d/01_init.sql
RUN echo "ALTER ROLE ${DB_USER} PASSWORD '${DB_PASSWORD}';" > /docker-entrypoint-initdb.d/02_init.sql
RUN echo "CREATE DATABASE ${DB_DATABASE};" > /docker-entrypoint-initdb.d/03_init.sql
RUN echo "\c ${DB_DATABASE}" >> /docker-entrypoint-initdb.d/03_init.sql
RUN echo "CREATE TABLE emails (\
    id SERIAL PRIMARY KEY,\
    email VARCHAR(255) NOT NULL\
    );" >> /docker-entrypoint-initdb.d/03_init.sql
RUN echo "CREATE TABLE phone_numbers (\
    id SERIAL PRIMARY KEY,\
    phone_number VARCHAR(20) NOT NULL\
    );" >> /docker-entrypoint-initdb.d/03_init.sql


RUN mkdir -p /var/log/postgres/ && chmod 777 /var/log/postgres/

CMD ["postgres", \
    "-c", "logging_collector=on",\
    "-c", "log_replication_commands=on",\
    "-c", "log_connections=on",\
    "-c", "log_directory=/var/log/postgres/",\
    "-c", "log_filename=postgres.log",\
    "-c", "wal_level=replica",\
    "-c", "hot_standby=on", \
    "-c", "max_wal_senders=10",\
    "-c", "max_replication_slots=10",\ 
    "-c", "hot_standby_feedback=on"]

