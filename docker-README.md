# Docker Setup for AIM Chatbot

This project has been dockerized to make deployment easier and more consistent across different environments.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Configuration

All configuration is done through environment variables, which can be set in the `.env` file or passed directly to Docker Compose.

### Available Environment Variables

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `AIM_USERNAME` | AIM username | xotrendbabeox |
| `AIM_PASSWORD` | AIM password | password |
| `AIM_SERVER` | AIM server address | aim.visionfun.org |
| `AIM_PORT` | AIM server port | 5190 |
| `DIFY_API_KEY` | Dify API key | app-5kmGGYfP4z0omMEfNYVaLW8B |
| `DIFY_API_URL` | Dify API URL | http://52.89.105.190/v1 |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | DEBUG |
| `LOG_FILE` | Log file path | logs/aimbot.log |

## Building and Running

### Build the Docker Image

```bash
docker-compose build
```

### Run the Container

```bash
docker-compose up -d
```

This will start the AIM chatbot in detached mode.

### View Logs

```bash
docker-compose logs -f
```

### Stop the Container

```bash
docker-compose down
```

## Volumes

The Docker Compose configuration mounts a volume for logs:

- `./logs:/app/logs`: Persists log files outside the container

## Customizing Configuration

You can customize the configuration by:

1. Editing the `.env` file
2. Passing environment variables when running Docker Compose:

```bash
AIM_USERNAME=myusername AIM_PASSWORD=mypassword docker-compose up -d
```

## Troubleshooting

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Ensure your environment variables are set correctly
3. Verify that the AIM server is accessible from the container
4. Check that the Dify API is accessible and the API key is valid
