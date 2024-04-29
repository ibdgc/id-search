"""CLI for IBDGC database"""

import click
from ibdgc_db import db
from ibdgc_db import loaders
from ibdgc_db import utils
from sqlalchemy.orm import Session
import pandas as pd
import os


@click.group()
def cli():
    """CLI for IBDGC database"""
    pass


@cli.command()
def init_db():
    """Initialize database."""
    db.init_db()


@cli.command()
def load_data():
    """Load data by executing all loaders."""
    for loader in loaders:
        if hasattr(loader, 'execute'):
            print(f'Executing loader {loader.__name__}...')
            loader.execute(db)


def list_choices():
    s = '\b\nAvailable indices:\n'
    for idx in utils.lookups.keys():
        s += f'  {idx}\n'
    centers = utils.get_centers()
    if centers:
        s += '\b\nCenters:\n'
        for center in centers:
            s += f'  {center}\n'
    return s



@cli.command(epilog=list_choices())
@click.option(
    '-i',
    '--index',
    default='registered_participant.consortium_id',
    show_default=True
)
@click.option(
    '-c',
    '--center',
    help='Restrict search to a given center.'
)
@click.argument('values', nargs=-1)  # Accept multiple values
def lookup(index, center, values):
    """Lookup participants by one of several indices for multiple values."""

    with Session(db.engine) as session:
        keys = utils.lookups[index]
        all_results = []

        for value in values:
            results = utils.get_participants(value, keys, session, center)
            for result in results:
                participant_data = utils.extract_participant_data(result)
                all_results.append(participant_data)

        if all_results:
            df = pd.DataFrame(all_results)
            print(df)

            # Create a temporary directory in the current working directory
            temp_dir = os.path.join(os.getcwd(), "tmp")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            # Define the CSV file path
            csv_file_path = os.path.join(temp_dir, "participants_lookup.csv")

            # Write to CSV
            df.to_csv(csv_file_path, index=False)
            print(f"Results have been saved to {csv_file_path}")
        else:
            print('No participants found')


@cli.command()
@click.argument('consortium_id')
@click.argument('alias')
def add_alias(consortium_id, alias):
    """Add alias for existing registered participant."""

    utils.add_alias(consortium_id, alias)


@cli.command()
@click.argument('alias')
def make_primary(alias):
    """Make alias the primary Consortium ID for that participant."""

    utils.make_primary(alias)


if __name__ == '__main__':
    cli()
