# cT_tradingbot




## Getting Started

These instructions will give you a copy of the project up and running on
your local machine for development and testing purposes. See deployment
for notes on deploying the project on a live system.

### Prerequisites

Requirements for the software and other tools to build, test and push 
- [Poetry](https://python-poetry.org/)
- [Python](https://www.python.org/)
- [matplotlib](https://matplotlib.org/)
- [pandas](https://pandas.pydata.org/)

### Installing

A step by step series of examples that tell you how to get a development
environment running

Download and install poetry 

    Windows

        (Invoke-WebRequest -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py -UseBasicParsing).Content | python -

    Mac OS/ Linux

        curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -

Avtivate virtual environment

    poetry shell

Install dependencies

    poetry install

Begin collecting data to be stored in sqlite db

    python main.py --feed <SYMBOL>

Once you have a sufficient amount of data

    python main.py --strat <SYMBOL>


## Authors

  - **Jacob Short** 


  - **Billie Thompson** - *Provided README Template* -
    [PurpleBooth](https://github.com/PurpleBooth)






