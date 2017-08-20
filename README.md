### Installation
Runs only on Python 3.6+. 
Clone or download the repository, then run something like
```
python3 -m venv /path/to/new/virtual/environment
pip3 install -r requirements.txt
# activate this new virtual environment before running the script
source /path/to/new/virtual/environment/bin/activate 
```

### Usage
You’ll need Trello credentials: key, secret, and token (thank OAuth for this). To get them, go to https://trello.com/app-key. Key is what you’ll see immediately after opening the page; to generate a token click “generate a token” link; to find secret be sure to scroll to the bottom of the page.
Open `config.conf` and replace sample values with the real ones.
Now you can run
```
python3 export.py "my trello board"
```

By default, all lists from the board are exported and saved to separate text files. See flags below for more on this behaviour.

### Flags

#### --lists, -l
Specify lists to export from the board:
```
python3 export.py --lists "To-Do, Closed" "my trello board"
```
Only cards from “To-Do” and “Closed” will be exported (to `to-do.txt` and `closed.txt`)

#### --prefix, -p
Add prefix to each exported card:
```
python3 export.py --prefix "User story" "my trello board"
```
You will get this:
```
User story 1. %card name%
%card description%

User story 2. %card name%
%card description%
```

By default, there are only numbers.

#### --no-numbering, -n
Automatic numbering can also be switched off:
```
python3 export.py --no-numbering "my trello board"
```
will result in
```
%card name%
%card description%

%card name%
%card description%
```

#### --comments, -c
Export comments as well:
```
python3 export.py --comments "my trello board"
```
For now, only the name of the comment’s author is exported:
```
1. %card name%
%card description%

Jane Doe: looks good.

2. %card name%
%card description%
```

#### --merge, -m
Export all lists into a single file:
```
python3 export.py --merge --lists "To-Do, Closed" "my trello board"
```
Instead of `to-do.txt` and `closed.txt` you will now get `my trello board.txt` containing cards from both lists.