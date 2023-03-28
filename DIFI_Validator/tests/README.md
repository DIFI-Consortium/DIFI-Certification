Copyright © `2022` `Kratos Technology & Training Solutions, Inc.`
Copyright © `2023` `Microsoft Corporation`
Licensed under the MIT License.
SPDX-License-Identifier: MIT

## How to run tests

In one terminal, launch app.py with:
```
cd DIFI_Validator
sudo pip install -r requirements.txt
python app.py
```

In a second terminal, run the tests with:
```
sudo pip install pytest
cd DIFI_Validator
python3 -m pytest tests/ --ipaddress="127.0.0.1"
```
