import Pyro4
import json
import urllib
import urllib.request
import atexit

# When this server starts it should check with the other servers and see which is the most up to date


@Pyro4.expose
class GreetingMaker(object):
    def get_food(self, json_input):
        try:
            with open("seccondary_server_1.json", "r") as myfile:
                data = myfile.read()
            obj = json.loads(data)
        except:
            obj = {}

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
        f = open("secondary_server_1.json", "w")
        obj[datetime]["address"] = js[0]["text"]
        json.dump(obj, f, indent=4)
        f.close()
        json_input[datetime]["address"] = js[0]["text"]

        save_unsynced("primary.server", json_input, datetime)
        save_unsynced("secondary.server1", json_input, datetime)

        return "Sending your food to {0}\n".format(js[0]["text"])

    def syncdata(self, json_input):
        if json_input is None:
            return None
        try:
            with open("secondary_server_1.json", "r") as myfile:
                data = myfile.read()
            obj = json.loads(data)
        except:
            obj = {}

        f = open("secondary_server_1.json", "w")
        datetime = list(json_input.keys())[0]
        obj[datetime] = json_input[datetime]
        json.dump(obj, f, indent=4)
        f.close()

    def get_unsynced(self, server):
        try:
            with open("secondary_server_1.json", "r") as myfile:
                data = myfile.read()
            obj = json.loads(data)
        except:
            return None
        return_obj = {}
        for i in obj[server]:
            return_obj[i] = obj[i]
        obj[server] = []
        f = open("secondary_server_1.json", "w")
        json.dump(obj, f, indent=4)
        f.close()
        return return_obj


def unregister():
    ns.remove("secondary.server1")


def save_unsynced(server, json_input, datetime):
    if server in list(ns.list()):
        secondary_server_1 = Pyro4.Proxy("PYRONAME:" + server)
        secondary_server_1.syncdata(json_input)
    else:
        with open("secondary_server_1.json", "r") as myfile:
            data = myfile.read()
        obj = json.loads(data)
        if (server + "_unsynced") in obj:
            obj[server + "_unsynced"].append(datetime)
        else:
            obj[server + "_unsynced"] = [datetime]
        f = open("secondary_server_1.json", "w")
        json.dump(obj, f, indent=4)
        f.close()


atexit.register(unregister)


daemon = Pyro4.Daemon()  # make a Pyro daemon
ns = Pyro4.locateNS()  # find the name server
uri = daemon.register(GreetingMaker)  # register the greeting maker as a Pyro object
ns.register(
    "secondary.server1", uri
)  # register the object with a name in the name server


def sync(servername):
    try:
        server = Pyro4.Proxy("PYRONAME:" + servername)
        unsynced = server.get_unsynced("secondary.server1_unsynced")
    except:
        return None
    if unsynced is None:
        return None
    try:
        with open("secondary_server_1.json", "r") as myfile:
            data = myfile.read()
        obj = json.loads(data)
    except:
        obj = {}

    f = open("secondary_server_1.json", "w")
    for datetime in list(unsynced.keys()):
        obj[datetime] = unsynced[datetime]
    json.dump(obj, f, indent=4)
    f.close()


sync("primary.server")
sync("secondary.server2")

daemon.requestLoop()  # start the event loop of the server to wait for calls
