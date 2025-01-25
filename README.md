# https://snowsune.net

Now I don't *really* intend for this to be an easily forkable build-your own site, I feel like too much of it is
going to be me dependant! Even still though, I'm committed to open-ness! And I will leave all the source code (or
as much of it as is feasible) fully open and *reviewable*. And if there are any every suggestions you would 
have for me I will be more than accepting of issues and bug reports in this repo!


## Hosting

I've set most things up for a sort of normal docker compose but, heres the sort of template
I use/expect to use!

```yml
services:
  db:
    image: postgres:15
    restart: "no"
    environment:
      - POSTGRES_USER=<user>
      - POSTGRES_PASSWORD=<password>
      - POSTGRES_DB=<dbname>
    healthcheck:
      test:
        ["CMD", "pg_isready", "-q", "-d", "<dbname>", "-U", "<user>"]
      interval: 10s
      timeout: 5s
      retries: 5
    logging:
      options:
        max-size: 10m
        max-file: "3"
    ports:
      - "5438:5432"
    volumes:
      - .local/data:/var/lib/postgresql/data

  snowsunenet:
    depends_on:
      db:
        condition: service_healthy
    image: ghcr..
    environment:
      LOG_LEVEL: "DEBUG"
      DATABASE_URL: postgres://<user>:<password>@db:5432/<dbname>
    restart: "no"
    command: "true"
```
