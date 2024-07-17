# DragonApp: Accelerating Backend Development

Welcome to DragonApp, an open-source project designed to streamline the development of backend APIs and AdminPanels. Tailored for organizations looking to deploy a single project or a cohesive set of functionalities, DragonApp leverages the power of the DragonAPI framework—an extension of FastAPI—to significantly reduce development time.

With DragonApp, developers can focus on crafting their unique application logic without getting bogged down by the intricacies of common backend features. From user account management to subscription services integration (e.g., Stripe), DragonApp provides built-in, ready-to-use functionalities that are essential for modern web applications.

While DragonApp is not intended as a Platform as a Service (PaaS) or Software as a Service (SaaS) solution for hosting multiple projects from various organizations, it excels as a robust foundation for any single project with a unified user base. Future updates aim to expand its capabilities, potentially allowing it to serve different projects to the same user base with configurable settings.

By making DragonApp open-source, we invite developers worldwide to contribute to its growth, ensuring it remains a cutting-edge tool that addresses real-world development challenges. Join us in making backend development faster, more efficient, and accessible to everyone.


## Configuration

1. Set the environment variables in `.env`. Docker will use the same file to set the environment variables in the container. Use `sample.env` as an example.


## Deployment for Production

Deployment uses Docker. 

1. Run `docker compose up -d` on first run. This will build the docker image, install the required packages and launch the container.
2. To update, after the latest files have been updated, you need to rebuild the image using `docker compose build`, then `docker compose up -d` to launch it. Or you can use `docker-compose up -d --build` to do both actions at once. You can also run multiple instance of RQ workers via `docker-compose up -d --build --scale worker=N` where N is the number of instances you would like to run, eg: 3.

You can view the terminal output by using `docker compose logs -f`.


## Deployment locally for Development
Using in local development. App will automatically reload on file changes.
```shell
sh run.sh 
# --worker argument to load the Redis workers (only works if Redis configuration is accessible)
# --upgrade argument to upgrade all dependencies 
```