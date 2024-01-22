import unittest
import API
import datetime

# Importing all necessary variables from API so that updated values are automatically updated in the tests as well
from API import (small_order_surcharge_limit, delivery_base_fee, devivery_base_fee_distance, num_items_charge,
                 delivery_fee_distance_increment, delivery_fee_distance_increment_charge,
                 num_items_charge_limit, bulk_items_limit, bulk_fee, rush_hour_weekday,
                 rush_hour_lower_time_limit, rush_hour_upper_time_limit, rush_hour_rate,
                 free_delivery_cart_value, max_delivery_fee)

#Helper function to generate ISO strings for tests. Generated date is next friday ;)
def generate_iso_date(weekday, hour, minutes):
    today = datetime.date.today()
    days_until_weekday = (weekday - today.weekday()) % 7
    if days_until_weekday < 0:
        days_until_weekday += 7
    target_date = today + datetime.timedelta(days=days_until_weekday)

    return datetime.datetime(target_date.year, target_date.month, target_date.day, hour, minutes).isoformat() + "Z"
     

class APITestCase(unittest.TestCase):

    def setUp(self):
        # Lets set up a client for testing
        self.app = API.app.test_client()
        self.app.testing = True
        
        # The dictionaries are somewhat convoluted, but allow the tests to update automatically if the API's fee calculation settings are changed
        self.distance_dict = {devivery_base_fee_distance: delivery_base_fee, # distance 1000, fee 200
                                devivery_base_fee_distance+(delivery_fee_distance_increment-1): delivery_base_fee+delivery_fee_distance_increment_charge, # distance 1499, fee 300
                                devivery_base_fee_distance+(delivery_fee_distance_increment): delivery_base_fee+delivery_fee_distance_increment_charge, # distance 1500, fee 300
                                devivery_base_fee_distance+(delivery_fee_distance_increment+1): delivery_base_fee+delivery_fee_distance_increment_charge*2 # distance 1501, fee 400
                                }
        self.num_items_fee_dict = {num_items_charge_limit-1: delivery_base_fee, # items 4, fee 200
                                    num_items_charge_limit: delivery_base_fee+num_items_charge, # items 5, fee 250
                                    num_items_charge_limit+1: delivery_base_fee+(num_items_charge*2), # items 6, fee 300
                                    bulk_items_limit-1: delivery_base_fee+(bulk_items_limit-1-(num_items_charge_limit-1))*num_items_charge, # items bulk limit -1 = 11, fee 550
                                    bulk_items_limit: delivery_base_fee+(bulk_items_limit-(num_items_charge_limit-1))*num_items_charge+bulk_fee, # items bulk limit = 12, fee 720
                                    bulk_items_limit+1: delivery_base_fee+(bulk_items_limit+1-(num_items_charge_limit-1))*num_items_charge+bulk_fee # items bulk limit +1 = 13, fee 770
                                    }
        self.small_order_dict = {small_order_surcharge_limit - (small_order_surcharge_limit-1): delivery_base_fee+small_order_surcharge_limit-1,
                                 small_order_surcharge_limit - 1: delivery_base_fee+small_order_surcharge_limit-(small_order_surcharge_limit-1),
                                 small_order_surcharge_limit: delivery_base_fee,
                                 }
        
        self.rush_hour_dict = {generate_iso_date(rush_hour_weekday, rush_hour_lower_time_limit-1, 59): delivery_base_fee, # Right date, before rush hour: no extra charge
                               generate_iso_date(rush_hour_weekday, rush_hour_lower_time_limit, 0): delivery_base_fee*rush_hour_rate, # Right date, start of rush hour, charge added
                               generate_iso_date(rush_hour_weekday, rush_hour_upper_time_limit-1, 59): delivery_base_fee*rush_hour_rate, # Right date, end of rush hour, charge added
                               generate_iso_date(rush_hour_weekday, rush_hour_upper_time_limit, 0): delivery_base_fee, # Right date, rush hour has ended, no extra charge
                               generate_iso_date(rush_hour_weekday-1, rush_hour_upper_time_limit-1, 0): delivery_base_fee # Wrong date, right time, no charge   
                               }
        
        self.free_delivery_dict = {free_delivery_cart_value-1: delivery_base_fee, # Less than free dilvery amount, normal fee
                                   free_delivery_cart_value: 0, # Exact free delivery cart value, free delivery fee
                                   free_delivery_cart_value+999999: 0 # Comically higher delivery cart value, free delivery fee
                                   }
        
        # Generating a ISO date to be used in the requests when no rush hour charge is wanted
        self.some_non_rush_hour_iso_date = generate_iso_date(rush_hour_weekday, rush_hour_lower_time_limit-1, 0)
        
        
    """
    Let's first test the API's aability to handle invalid request data
    """
    def test_missing_parameter(self):
        response = self.app.post('/delivery_fee', json={
            "delivery_distance": 2235,
            "number_of_items": 4,
            "time": self.some_non_rush_hour_iso_date
        })
        data = response.get_json()
        self.assertEqual(response.status_code, 400) # The API should return 400, as the request is missing a parameter
        self.assertEqual(data['error'], "Invalid data format") # Check that the correct error is returned
        
    def test_invalid_cartValue(self):
        response = self.app.post('/delivery_fee', json={
            "cart_value": -1,
            "delivery_distance": 2235,
            "number_of_items": 4,
            "time": self.some_non_rush_hour_iso_date
        })
        data = response.get_json()
        self.assertEqual(response.status_code, 400) # The API should return 400, as the request cart_value is negative
        self.assertEqual(data['error'], "Negative values are not allowed") # Check that the correct error is returned

    def test_invalid_timeStamp(self):
        response = self.app.post('/delivery_fee', json={
            "cart_value": 1,
            "delivery_distance": 2235,
            "number_of_items": 4,
            "time": "2024-1-1 17:00:00"
        })
        data = response.get_json()
        self.assertEqual(response.status_code, 400) # The API should return 400, as the request timestamp is non-ISO format
        self.assertEqual(data['error'], "Time is not in valid ISO format") # Check that the correct error is returned
        
    """
    Confirming that the API calculated delivery fee correctly
    """
    
    # All other parameters are set, so no other charge should apply other than initial delivery charge
    def test_initial_delivery_fee(self):
        response = self.app.post('/delivery_fee', json={
            "cart_value": small_order_surcharge_limit,
            "delivery_distance": 1,
            "number_of_items": 1,
            "time": self.some_non_rush_hour_iso_date
        })
        data = response.get_json()
        self.assertEqual(response.status_code, 200) # The API should return 200, as the request is valid
        self.assertEqual(data['delivery_fee'], 200) # verify the delivery fee
        
    # Testing that delivery fee is calculated correctly for 1499, 1500 and 1501 distances.
    def test_distance_added_delivery_fee(self):
        for i, j in self.distance_dict.items(): # This dictionary contains the distance and expected delivery fee
            response = self.app.post('/delivery_fee', json={
                "cart_value": small_order_surcharge_limit,
                "delivery_distance": i,
                "number_of_items": 1,
                "time": self.some_non_rush_hour_iso_date
            })
            data = response.get_json()
            self.assertEqual(response.status_code, 200) # The API should return 200, as the request is valid
            self.assertEqual(data['delivery_fee'], j) # verify the delivery fee
    
    # Testing that small order surcharge is calculated correctly
    def test_small_order_surcharge(self):
        for i, j in self.small_order_dict.items(): # This dictionary contains the cart_value and expected delivery fee
            response = self.app.post('/delivery_fee', json={
                "cart_value": i,
                "delivery_distance": 1,
                "number_of_items": 1,
                "time": self.some_non_rush_hour_iso_date
            })
            data = response.get_json()
            self.assertEqual(response.status_code, 200) # The API should return 200, as the request is valid
            self.assertEqual(data['delivery_fee'], j) # verify the delivery fee
    
    # Testing that API handles bulk charge and items amount charge correctly.    
    def test_num_items_surcharge(self):
        for i, j in self.num_items_fee_dict.items(): # This dictionary contains the number_of_items and expected delivery fee
            response = self.app.post('/delivery_fee', json={
                "cart_value": small_order_surcharge_limit,
                "delivery_distance": 1,
                "number_of_items": i,
                "time": self.some_non_rush_hour_iso_date
            })
            data = response.get_json()
            self.assertEqual(response.status_code, 200) # The API should return 200, as the request is valid
            self.assertEqual(data['delivery_fee'], j) # verify the delivery fee
            
    # Testing that API handles the rush hour charges correctly
    def test_rush_hour_surcharge(self):
        for i, j in self.rush_hour_dict.items(): # This dictionary contains the ISO date timestaps and expected delivery fee
            response = self.app.post('/delivery_fee', json={
                "cart_value": small_order_surcharge_limit,
                "delivery_distance": 1,
                "number_of_items": 1,
                "time": i
            })
            data = response.get_json()
            self.assertEqual(response.status_code, 200) # The API should return 200, as the request is valid
            self.assertEqual(data['delivery_fee'], j) # verify the delivery fee
          
    # Testing that a free delivery is hanled correctly  
    def test_over_200_cart(self):
        for i, j in self.free_delivery_dict.items(): # This dictionary contains the cart_value and expected delivery fee
            response = self.app.post('/delivery_fee', json={
                "cart_value": i,
                "delivery_distance": 1,
                "number_of_items": 1,
                "time": self.some_non_rush_hour_iso_date
            })
            data = response.get_json()
            self.assertEqual(response.status_code, 200) # The API should return 200, as the request is valid
            self.assertEqual(data['delivery_fee'], j) # verify the delivery fee
            
    def test_over_limit_delivery_fee(self):
        response = self.app.post('/delivery_fee', json={
            "cart_value": 1,
            "delivery_distance": 9999,
            "number_of_items": 20,
            "time": self.some_non_rush_hour_iso_date
        })
        data = response.get_json()
        self.assertEqual(response.status_code, 200) # The API should return 200, as the request is valid
        self.assertEqual(data['delivery_fee'], max_delivery_fee) # The delivery fee should not be more than max limit
        
# All tests ran
if __name__ == '__main__':
    unittest.main(verbosity=2)