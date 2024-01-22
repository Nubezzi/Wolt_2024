from flask import Flask, request, jsonify
from datetime import datetime
import json
import sys 

app = Flask(__name__)
port_num = 5000 # Port on which the API service is ran

# Applying a custom port from system args
if len(sys.argv) > 1:
    port_num = sys.argv[1]
    
# Initializing variables for different limits
# In a real use case, these values would not be hard coded, but for this assignment this will do.
small_order_surcharge_limit = 1000 # 10€
delivery_base_fee = 200 # 2€
devivery_base_fee_distance = 1000 # 1km, 1000m
delivery_fee_distance_increment = 500 # 500m
delivery_fee_distance_increment_charge = 100 # 1€
num_items_charge_limit = 5 # after this amount of items are in cart, a additional charge is applied for each additional item 
num_items_charge = 50 # additional charge, 0.5€
bulk_items_limit = 12 # item limit for bulk charge
bulk_fee = 120 # 1.2€
rush_hour_weekday = 4 # monday 0, tuesday 1... etc
rush_hour_lower_time_limit = 15 # starting hour of "rush hour"
rush_hour_upper_time_limit = 19 # ending hour of "rush hour"
rush_hour_rate = 1.2 # delivery fee multiplier for "rush hour"
free_delivery_cart_value = 20000 # free delivery cart value. 200€

def small_order_surcharge(cart_value):
    if cart_value < small_order_surcharge_limit:
        # The surcharge is the difference between the cart value and 10€
        return small_order_surcharge_limit - cart_value
    return 0

def calculate_delivery_distance_fee(delivery_distance):
    base_fee = delivery_base_fee  # base fee is 2€. This is used for all orders with delivery distance => 1km
    if delivery_distance <= devivery_base_fee_distance:
        return base_fee
    else:
        # Calculate additional distance beyond 1000 meters
        additional_distance = delivery_distance - devivery_base_fee_distance
        # Calculate additional fees for every 500 meters (or part thereof)
        additional_fees = -(-additional_distance // delivery_fee_distance_increment) * delivery_fee_distance_increment_charge  # 1€ in cents
        return base_fee + additional_fees
    
def cart_items_charge(number_of_items):
    items_charge = (number_of_items - (num_items_charge_limit - 1)) * num_items_charge if number_of_items >= num_items_charge_limit else 0
    items_charge += bulk_fee if number_of_items >= bulk_items_limit else 0
    return items_charge


def rush_hour_charge(time_str):
    # Parse the time string to a datetime object
    time_obj = datetime.fromisoformat(time_str)
    # Check if it's Friday (weekday() returns 4 for Friday) and during rush hours (15:00 to 19:00 UTC)
    return time_obj.weekday() == rush_hour_weekday and rush_hour_lower_time_limit <= time_obj.hour < rush_hour_upper_time_limit


@app.route('/delivery_fee', methods=['POST'])
def calculate_delivery_fee():
    data = request.json

    # Validating the data from the request
    try:
        cart_value = int(data['cart_value'])
        delivery_distance = int(data['delivery_distance'])
        number_of_items = int(data['number_of_items'])
        time = data['time']
        
        # Negative values not accepted
        if cart_value < 0 or delivery_distance < 0 or number_of_items < 0:
            return jsonify({"error": "Negative values are not allowed"}), 400

        # verify timestamp iso format
        try:
            datetime.fromisoformat(time)
        except ValueError:
            return jsonify({"error": "Time is not in valid ISO format"}), 400

    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Invalid data format"}), 400
    
    delivery_fee = 0
    
    
    # Check small order surcharge (100 = 1€, 1000 = 10€ etc...). Small order surcharge applies when order is less than 10€
    delivery_fee += small_order_surcharge(cart_value)
        
    # Additional delivery fee based on distance. 2€ for the 1st 1km is mandatory. Every starting 500m after that adds 1€
    delivery_fee += calculate_delivery_distance_fee(delivery_distance)
        
    # Adding charges based on number of items in the cart, bulk charge also
    delivery_fee += cart_items_charge(number_of_items)
    
    # Multiplying charge if time is friday rush hour
    delivery_fee = delivery_fee * rush_hour_rate if rush_hour_charge(time) else delivery_fee
    
    # If delivery fee is over 15€, set it to 15€
    delivery_fee = min(delivery_fee, 1500)
    
    # Lastly quick check to verify if free delivery is necessary.
    if cart_value >= free_delivery_cart_value:
        delivery_fee = 0

    return jsonify({"delivery_fee": delivery_fee})

if __name__ == '__main__':
    app.run(debug=True, port=port_num)