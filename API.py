from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

def small_order_surcharge(cart_value):
    if cart_value < 1000:
        # The surcharge is the difference between the cart value and 10€
        return 1000 - cart_value
    return 0

def calculate_delivery_distance_fee(delivery_distance):
    base_fee = 200  # base fee is 2€. This is used for all orders with delivery distance => 1km
    if delivery_distance <= 1000:
        return base_fee
    else:
        # Calculate additional distance beyond 1000 meters
        additional_distance = delivery_distance - 1000

        # Calculate additional fees for every 500 meters (or part thereof)
        additional_fees = -(-additional_distance // 500) * 100  # 1€ in cents

        return base_fee + additional_fees
    
def cart_items_charge(number_of_items):
    items_charge = (number_of_items - 4) * 50 if number_of_items >= 5 else 0
    items_charge += 120 if number_of_items >= 12 else 0
    return items_charge


def rush_hour_charge(time_str):
    # Parse the time string to a datetime object
    time_obj = datetime.fromisoformat(time_str)

    # Check if it's Friday (weekday() returns 4 for Friday) and during rush hours (15:00 to 19:00 UTC)
    return time_obj.weekday() == 4 and 15 <= time_obj.hour < 19


@app.route('/delivery_fee', methods=['POST'])
def calculate_delivery_fee():
    data = request.json

    # Validating the data from the request
    try:
        cart_value = int(data['cart_value'])
        delivery_distance = int(data['delivery_distance'])
        number_of_items = int(data['number_of_items'])
        time = data['time']
        
        # Negative cart values not accepted
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
    print(f"added {small_order_surcharge(cart_value)}")
    delivery_fee += small_order_surcharge(cart_value)
        
    # Additional delivery fee based on distance. 2€ for the 1st 1km is mandatory. Every starting 500m after that adds 1€
    print(f"added {calculate_delivery_distance_fee(delivery_distance)}")
    delivery_fee += calculate_delivery_distance_fee(delivery_distance)
        
    # Adding charges based on number of items in the cart, bulk charge also
    print(f"added {cart_items_charge(number_of_items)}")
    delivery_fee += cart_items_charge(number_of_items)
    
    # Multiplying charge if time is friday rush hour
    print(f"is rushtime: {rush_hour_charge(time)}")
    delivery_fee = delivery_fee * 1.2 if rush_hour_charge(time) else delivery_fee
    
    # If delivery fee is over 15€, set it to 15€
    delivery_fee = min(delivery_fee, 1500)

    return jsonify({"delivery_fee": delivery_fee})

if __name__ == '__main__':
    app.run(debug=True)