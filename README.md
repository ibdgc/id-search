# id-search

### Description

The companion querying tool for the IBDGC ID association database (https://github.com/ibdgc/ibdgc-db). Features of this application were forked from a subset of the ibdgc-db codebase for the sake of simplification by separating less restricted query access from more restricted database provisioning. Functionality maintained here generally revolves around the `lookup` command.

### Installation

The package should be installed from the source repo. Clone the repo, and execute the pip install. It's strongly encouraged that you use some type of environment management like venv or conda.

```
# setup your env (venv/conda)

# clone the repo
git clone https://github.com/ibdgc/id-search.git

# install from the project root
cd id-search
pip install .
```

### Configuration

This tool requires the presence of the `ibdgc.db` database. The database is rebuilt weekly and can be found in the IBDGC OSF Collection as a component of the ID Tracking project. Access to this database is restricted to IBDGC members and collaborators. Please contact the DCC

1. Download the ID database found at this project component: (https://osf.io/gmnfk/)
1. Place the database in the `tmp` directory under the id-search project root

```
mv ibdgc.db id-search/tmp
```

### Usage
