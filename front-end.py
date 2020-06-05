# saved as front-end.py
# So what I want is for this code to call one server (primary server), and if that server isn't available
# loop through the other servers, if none are available then return an error


import Pyro4
import random
import atexit


@Pyro4.expose
class GreetingMaker(object):
    def get_food(self, name):
        available_severs = list(ns.list())
        print(available_severs)
        if "primary.server" in available_severs:
            print("Going with the primary server")
            server = Pyro4.Proxy("PYRONAME:primary.server")
        else:
            secondary_servers = ["secondary.server1", "secondary.server2"]
            available_secondary_servers = [
                value for value in secondary_servers if value in available_severs
            ]
            if len(available_secondary_servers) == 0:
                print("No servers available")
                return "No available servers"
            else:
                print("Selected alternate server")
                server = Pyro4.Proxy(
                    "PYRONAME:" + random.choice(available_secondary_servers)
                )

        print("Doing stuff")
        return server.get_food(name)


def unregister():
    ns.remove("fe.server")


atexit.register(unregister)
daemon = Pyro4.Daemon()  # make a Pyro daemon
ns = Pyro4.locateNS()  # find the name server
uri = daemon.register(GreetingMaker)  # register the greeting maker as a Pyro object
ns.register("fe.server", uri)  # register the object with a name in the name server
print("Ready.")
daemon.requestLoop()  # start the event loop of the server to wait for calls
