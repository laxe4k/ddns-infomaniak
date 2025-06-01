# Infomaniak DDNS Updater

This Python script automatically updates your Infomaniak DNS records with your current public IP address. It supports both IPv4 and IPv6.

## Features

*   Retrieves current public IPv4 and IPv6 addresses.
*   Compares current public IP with the IP resolved from the configured hostname.
*   Updates Infomaniak DNS record if the IP address has changed.
*   Configurable via environment variables.
*   Docker support for easy deployment.

## Prerequisites

*   Python 3.x
*   `requests` Python library

## Configuration

The script is configured using environment variables. Create a `.env` file in the project root or set these variables in your environment:

*   `INFOMANIAK_DDNS_HOSTNAME`: The hostname you want to update (e.g., `yourdomain.com` or `sub.yourdomain.com`).
*   `INFOMANIAK_DDNS_USERNAME`: Your Infomaniak API username (often the same as your login).
*   `INFOMANIAK_DDNS_PASSWORD`: Your Infomaniak API password or a token if supported.

Example `.env` file:
```
INFOMANIAK_DDNS_USERNAME=your_username
INFOMANIAK_DDNS_PASSWORD=your_password
INFOMANIAK_DDNS_HOSTNAME=your.domain.com
```

## Usage

### Running directly

1.  Ensure Python 3 and `pip` are installed.
2.  Install the required library:
    ```sh
    pip install -r requirements.txt
    ```
3.  Set the environment variables as described in the Configuration section (e.g., by creating a `.env` file or exporting them in your shell).
4.  Run the script:
    ```sh
    python ddns.py
    ```

### Running with Docker

1.  Build the Docker image:
    ```sh
    docker build -t infomaniak-ddns .
    ```
2.  Run the Docker container, passing the environment variables:
    ```sh
    docker run --rm \
      -e INFOMANIAK_DDNS_HOSTNAME="your.domain.com" \
      -e INFOMANIAK_DDNS_USERNAME="your_username" \
      -e INFOMANIAK_DDNS_PASSWORD="your_password" \
      infomaniak-ddns
    ```
    Alternatively, you can use an environment file with Docker:
    ```sh
    docker run --rm --env-file .env infomaniak-ddns
    ```

By default, the script processes IPv4 updates. To enable IPv6 updates, you will need to uncomment the relevant line in the `ddns.py` script:
```python
// filepath: a:\kDrive\Développement\Laxe4k\ddns\ddns.py
// ...existing code...
    # Traitement IPv4
    process_ddns_update(4, target_hostname, infomaniak_username, infomaniak_password, ipaddress)

    # Traitement IPv6 - Comment out this line to skip IPv6 processing
    process_ddns_update(6, target_hostname, infomaniak_username, infomaniak_password, ipaddress) # Uncomment this line

    print("\nScript terminé.")
```

## Project Files

*   [`ddns.py`](a:\kDrive\Développement\Laxe4k\ddns\ddns.py): The main Python script for DDNS updates.
*   [`Dockerfile`](a:\kDrive\Développement\Laxe4k\ddns\Dockerfile): For building the Docker image.
*   [`requirements.txt`](a:\kDrive\Développement\Laxe4k\ddns\requirements.txt): Python dependencies.
*   [`.env`](a:\kDrive\Développement\Laxe4k\ddns\.env): Example environment variable file (ignored by Git).
*   [`LICENSE`](a:\kDrive\Développement\Laxe4k\ddns\LICENSE): Project license.
*   [`README.md`](a:\kDrive\Développement\Laxe4k\ddns\README.md): This file.

## License

This project is licensed under the MIT License - see the [LICENSE](a:\kDrive\Développement\Laxe4k\ddns\LICENSE) file for details.