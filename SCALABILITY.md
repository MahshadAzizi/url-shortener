# Scalability

## 1. How would you handle logging if logging every request becomes too expensive?
The application should never write every request log directly to the primary PostgreSQL database.

For redirect/visit analytics, I would treat those as events rather than regular application logs. At higher traffic, I would replace BackgroundTasks with a durable message queue such as Kafka or RabbitMQ:
````
Redirect request
      |
      +----> response immediately
      |
      v
   message queue
      |
      v
 analytics consumer
      |
      v
 analytics storage

````

## 2. What would you change if the service had to run on multiple server instances?
The application is designed to be stateless, so multiple FastAPI instances can run behind a load balancer:

````
                 Load Balancer
                /      |      \
               /       |       \
             API #1  API #2  API #3
               \       |       /
                \      |      /
                 PostgreSQL
````

No application state should be stored in process memory that another instance needs.

Each instance creates its own SQLAlchemy engine and connection pool.

The database remains the shared source of truth.

The main consideration is database connection capacity.
For example:
````
3 API instances
pool_size = 10
max_overflow = 5

Maximum possible connections:

3 × (10 + 5) = 45
````

herefore, connection pool sizes must be configured based on the number of application instances and PostgreSQL's connection limits.

If the number of instances grows substantially, I would consider a connection pooler such as PgBouncer.

For the read-heavy redirect endpoint, I would introduce Redis:

````
              Load Balancer
                    |
              API instances
                    |
                  Redis
                /       \
             HIT         MISS
              |            |
           redirect     PostgreSQL
````

Because short URLs are mostly immutable, they are a good candidate for caching.

If PostgreSQL read traffic becomes a bottleneck, read replicas could also be introduced, while keeping writes on the primary database.

## 3. What would you do if traffic became very heavy during a marketing campaign (thousands of requests per second)?
The first priority would be protecting the redirect path because:

````
GET /{short_code}
````
is the most latency-sensitive and potentially highest-volume operation.

I would keep the synchronous path as small as possible:

````
Request
   |
   v
Redis lookup
   |
   +---- HIT ----> redirect immediately
   |
   +---- MISS ---> PostgreSQL
````
Frequently accessed short codes would therefore be served from Redis instead of hitting PostgreSQL for every request.
Visit recording should not block the redirect response.

At high traffic, I would replace the current background task with a durable queue:
````
                     API
                      |
              +-------+-------+
              |               |
              v               v
          Redirect         Message Queue
          response              |
                                v
                         Visit consumers
                                |
                                v
                         Analytics storage
````
This allows consumers to process visit events independently and scale them according to queue depth.