import Pyro4
import json
import urllib
import urllib.request
import atexit

# This server starts
# Checks with the other servers if they have recorded data that they processed
# Pull in all that data and put it into the main JSON
# Push the JSON out to each of the secondary servers
# It can also call this function before it does any history output


@Pyro4.expose
class GreetingMaker(object):
    def get_food(self, json_input):
        sync("secondary.server1")
        sync("secondary.server2")
        try:
            with open("primary_server_data.json", "r") as myfile:
                data = myfile.read()
            obj = json.loads(data)
        except:
            obj = {}

        request_type = json_input.pop("request")
        if request_type == "R":
            timestamps_unprocessed = list(obj.keys())
            timestamps = [time for time in timestamps_unprocessed if time[-1] != "d"]
            timestamps = sorted(timestamps, reverse=True)
            food = []
            house_number = []
            address = []
            for date in timestamps[:10]:
                food.append(obj[date]["food"])
                house_number.append(obj[date]["house_number"])
                address.append(obj[date]["address"])
            import pandas as pd

            data = {"Food": food, "House_Number": house_number, "Address": address}
            df = pd.DataFrame(data)
            return df.to_string()
        datetime = list(json_input.keys())[0]
        obj[datetime] = json_input[datetime]

        try:
            j = urllib.request.urlopen(
                "https://getaddress.io/google/GetAutocompletePostcodes?q={0}".format(
                    json_input[datetime]["postcode"].replace(" ", "")
                )
            )
        except:
            return "Could not contact the Postcode API"

        str_response = j.read().decode("utf-8")
        try:
            js = json.loads(str_response)
        except:
            return "The API did not return a valid response"

        if not js:
            return "Invalid postcode"
        f = open("primary_server_data.json", "w")
        obj[datetime]["address"] = js[0]["text"]
        json.dump(obj, f, indent=4)
        f.close()
        json_input[datetime]["address"] = js[0]["text"]
        save_unsynced("secondary.server1", json_input, datetime)
        save_unsynced("secondary.server2", json_input, datetime)

        return "Sending your food to {0}\n".format(js[0]["text"])

    def syncdata(self, json_input):
        if json_input is None:
            return None

        try:
            with open("primary_server_data.json", "r") as myfile:
                data = myfile.read()
            obj = json.loads(data)
        except:
            obj = {}

        f = open("primary_server_data.json", "w")
        datetime = list(json_input.keys())[0]
        obj[datetime] = json_input[datetime]
        json.dump(obj, f, indent=4)
        f.close()

    def get_unsynced(self, server):
        try:
            with open("primary_server_data.json", "r") as myfile:
                data = myfile.read()
            obj = json.loads(data)
        except:
            return None
        return_obj = {}
        for i in obj[server]:
            return_obj[i] = obj[i]
        obj[server] = []
        f = open("primary_server_data.json", "w")
        json.dump(obj, f, indent=4)
        f.close()
        return return_obj


def unregister():
    ns.remove("primary.server")


def save_unsynced(server, json_input, datetime):
    if server in list(ns.list()):
        secondary_server_1 = Pyro4.Proxy("PYRONAME:" + server)
        secondary_server_1.syncdata(json_input)
    else:
        with open("primary_server_data.json", "r") as myfile:
            data = myfile.read()
        obj = json.loads(data)
        if (server + "_unsynced") in obj:
            obj[server + "_unsynced"].append(datetime)
        else:
            obj[server + "_unsynced"] = [datetime]
        f = open("primary_server_data.json", "w")
        json.dump(obj, f, indent=4)
        f.close()


atexit.register(unregister)
daemon = Pyro4.Daemon()  # make a Pyro daemon
ns = Pyro4.locateNS()  # find the name server
uri = daemon.register(GreetingMaker)  # register the greeting maker as a Pyro object
ns.register("primary.server", uri)  # register the object with a name in the name server


def sync(servername):
    try:
        server = Pyro4.Proxy("PYRONAME:" + servername)
        unsynced = server.get_unsynced("primary.server_unsynced")
    except:
        return None
    if unsynced is None:
        return None
    try:
        with open("primary_server_data.json", "r") as myfile:
            data = myfile.read()
        obj = json.loads(data)
    except:
        obj = {}

    f = open("primary_server_data.json", "w")
    for datetime in list(unsynced.keys()):
        obj[datetime] = unsynced[datetime]
    json.dump(obj, f, indent=4)
    f.close()


sync("secondary.server1")
sync("secondary.server2")


daemon.requestLoop()  # start the event loop of the server to wait for calls
