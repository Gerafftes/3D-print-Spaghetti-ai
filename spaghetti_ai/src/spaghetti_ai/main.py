import logging

from .config import Settings
from .service import SpaghettiService


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    SpaghettiService(Settings.from_environment()).run()


if __name__ == "__main__":
    main()
