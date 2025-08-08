from models.ddns_client import from_env


def main() -> None:
    client = from_env()
    client.run_forever()


if __name__ == "__main__":
    main()
