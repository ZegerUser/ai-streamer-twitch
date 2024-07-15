import asyncio
import click
import toml
import logging
from pathlib import Path

from .service import Service
from .config import ServerConfig

@click.command()
@click.option('--config', '-c', type=click.Path(exists=True), required=True, help='Path to the TOML configuration file')
@click.option('--log-level', '-l', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']), default='INFO', help='Set the logging level')
def main(config: str, log_level: str):
    config_path = Path(config)
    server_config = ServerConfig(config_path)

    logging_level = getattr(logging, log_level.upper())

    service = Service(server_config, log_level=logging_level)

    async def run_service():
        try:
            await service.start()
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            click.echo("Shutting down the service...")
        finally:
            await service.stop()

    asyncio.run(run_service())

if __name__ == "__main__":
    main()