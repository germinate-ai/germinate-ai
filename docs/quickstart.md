
## Requirements

- A running [NATS.io](https://nats.io/) cluster
- A running Postgres DB (See included `docker-compose.yml` file)
- Poetry
- (Optional for now) A Weaviate instance (See included `docker-compose.yml` file)

## Quickstart

0. Clone the repo, and install dependencies with poetry.

    ```bash
    poetry install
    ```


1. Run the NATS Jetstream cluster.

    You can simply use the NATS CLI to run a test cluster:
    ```bash
    nats server --jetstream
    ```

2. Run Postgres.

    You can use the included `docker-compose.yml` file:
    ```bash
    docker compose --profile postgres up -d
    ```

3. Create a `.env` file in `./` based on the included `.env.example` file.


4. Run the coordinator process.

    ```bash
    poetry run germinate coordinator
    ```

    The coordinator updates state, and triggers state transitions/enqueues tasks as appropriate based on your Workflow state machine + tasks DAGs definitions.


5. Run one or more workers.

    ```bash
    poetry run germinate worker
    ```

    Workers execute tasks that are assigned to them.

6. Run a workflow.

    ```bash
    poetry run germinate workflow germinate_ai.workflows.metagpt.main '{"product_requirements": "A simple tictactoe game using Pygame"}' 
    ```

TEMP: Ideally, you would be able to create workflows in your own project and use Germinate as a framework. But, until we implement pickling and sending task executors over the wire to remote workers, its easiest to write workflows in `./germinate_ai/workflows` and execute them as shown above.

The last argument is the input to the first set of tasks in the workflows initial state's tasks DAG.

Refer to `./germinate_ai/workflows/metagpt` to see our (WIP) first example workflow.

## Commands

Temporary limited CLI:

* `germinate coordinator` - Start the Coordinator process.
* `germinate worker` - Start the Worker process.
* `germinate workflow germinate_ai.workflows.metagpt.main` - Enqueue the simple MetaGPT-(ish) workflow.
* `germinate db` - Create all Postgres tables.
* `germinate --help` - Print help message and exit.
