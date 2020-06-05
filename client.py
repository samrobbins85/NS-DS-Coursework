# saved as greeting-client.py
import Pyro4
import datetime
import sys

r_or_s = input("Would you like to Retrieve(R) or Submit(S) an order ")
if r_or_s == "S":
    Food = input("What food do you want to order ")
    House_number = input("What is your house number ").strip()
    Postcode = input("What is your postcode ").strip()
    json_output = {
        "request": "S",
        datetime.datetime.now().isoformat(): {
            "food": Food,
            "house_number": House_number,
            "postcode": Postcode,
        },
    }
elif r_or_s == "R":
    json_output = {"request": "R"}
else:
    print("Invalid command")
    sys.exit()


greeting_maker = Pyro4.Proxy(
    "PYRONAME:fe.server"
)  # use name server object lookup uri shortcut
print(greeting_maker.get_food(json_output))
