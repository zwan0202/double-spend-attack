# Double Spend Attack

## Dependencies

Python: download from https://python.org

pip package manager - By default, pip is installed into the current virtual environment (if one is active) 
or into the system site packages (if there is no active virtual environment). 
If not, run the following from your command line

```
python -m ensurepip
```

This will install pip globally. Then you can install project-specific dependencies as follows

### Installing

Clone the repo, then:

```bash
pip install -r requirements.txt
```

This will install all dependencies required to run the python server.

## Run

- Temp storage manager for data exchange (run once)

```bash
python temp_storage_manager.py
```

- Blockchain node

```bash
python server.py
```

- User

```bash
python client.py
```

## Usage

After running `client.py` 

- For miner, select `1` to start auto mining

- For attacker, select `2` to perform double spend attack, runs `1` hour

### Config

In `constant.py`

- `DSA_TIMEOUT` : Set double spend attack timeout in `second`, will terminate current DSA
 and start a new one

- `DIFFICULTY` : Difficulty for PoW