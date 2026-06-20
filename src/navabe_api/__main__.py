from navabe_api import create_app


def main() -> None:
    create_app().run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()

