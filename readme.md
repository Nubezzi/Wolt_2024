# Wolt 2024 Delivery Fee Python API

Wolt Summer 2024 Engineering Internships preminary assignment

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for assesment and testing purposes.

### Prerequisites

What things you need to install the software and how to install them:

- Python 3 (3.11.5 was used)
- Flask (2.3.2)

### Installing

If a compatible Flask version is not installed, it can be installed by running this in the project root directory:

```
pip install -r requirements.txt
```

The latest version of Flask should also work without issue:

```
pip install flask
```

## Usage

### Running the server

To start the Flask server, run:

```
python API.py   or      python3 API.py
```

This starts a Flask server on localhost:5000. 
a Custom port can be used instead by passing the desired port a launch argument:

```
python API.py 8001
```

### Accessing the endpoint

accessing the delivery fee endpoint can be achieved by POSTing to localhost:port/delivery_fee with the correct json formatted request body:

```
{
    "cart_value": 790,
    "delivery_distance": 2235, 
    "number_of_items": 4, 
    "time": "2024-01-15T13:00:00Z"
}
```

API responds with either:
```
{"delivery_fee": 710}
```
for succesful requests and:
```
{"error": "Error description"}
```
to invalid requests.

### Modifying the delivery fee calculation settings

Settings used for delivery fee calculations are simply stored as variables that are defined in the beginning of API.py. These can be modified to suit needed changes.
In a real use case these values would not be hard coded, but for this assignment this will do. 

## Tests

Automated tests for testing the API functionality have been coded in API_tests.py
unittest library should be included in the python installation so it doesnt need an additional dependencies.

The tests test all critical functionality of the API and use the defined calculation settings variables from the api to automatically stay up to daste even if the settings are updated.

### Running tests

tests can be simply run with: 

```
python API_tests.py
```

## Author

* **Paavo Nurminen** - [portfolio](https://paavonurminen.fi) - [LinkedIn](https://www.linkedin.com/in/paavo-nurminen-0318301b9/)
