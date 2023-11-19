# ah-grinder
For fetching auction house data in world of warcraft

# ah-analyzer
For analyzing auction house data in world of warcraft

# TODO

min quantity is always at least one atm. make sure that each item has at least None auctions at every day.
maybe have a list of all item ids and scan the auction data for all items in this list. hence some items will have
zero auctions and then this will be recorded for the analysis.

# Other info
1. auctions are updated once every hour. The last_modified info the the auction api response has
been seen to been varying number of minutes passed the hour. e.g. 4,5,17,18.

2. the command for copying from the pi is
```
scp pi@raspberrypi.local:~/auctions* data/.
```

3. to copy from the pi and not overwrite existing files, use
```
rsync -av --ignore-existing pi@raspberrypi.local:~/auctions* data/
```

explanation:
-av: Archive mode with verbose output.
--ignore-existing: Skip files that already exist at the destination.
pi@raspberrypi.local:~/auctions*: Source path on the remote server. This assumes you are copying files matching the pattern auctions* from the home directory of the pi user on the Raspberry Pi.
data/: Destination directory on your local machine.
This rsync command will only copy files that don't already exist in the destination directory (data/), similar to the -n option in scp.
