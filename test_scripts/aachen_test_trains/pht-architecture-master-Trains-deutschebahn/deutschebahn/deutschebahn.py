
import time

print("Printed immediately.")
for i in range(1000):
    time.sleep(1)
    print("Printed after {} seconds.".format(i))
