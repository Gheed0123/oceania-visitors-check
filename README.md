This script checks a list of supplied names with the friends ingame using fuzzy matching.

fuzzy matching meaning you do not have to type in the names correctly :)

Now you can view your visitors sorted by reputation. 

I use this to do friendrun faster.

How to use:
* Need Python , and install the libraries. I used Python 3.9.16
* Type in a name in 'visitors.txt' on a new line, no need to type super accurately.
* Use the separator '----' to specify a new day.
* Update friends.json in your first run, and every so often to keep it accurate.
* Run the script.

You can get the friends.json as follows in Firefox:
* Press F12 to open up the console
* Switch to network tab
* Load up the game
* Type in friends
* Right click the POST, -> Copy value -> Copy response
* Save this to the friends.json file

Note, fuzzy matching is not 100% accurate, but you can verify the output yourself. 

An example is show in example_output.png

The first column shows the friend name, second column the reputation, third column the input
