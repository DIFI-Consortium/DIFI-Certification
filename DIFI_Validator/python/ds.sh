# Copyright © `2022` `Kratos Technology & Training Solutions, Inc.`
# Licensed under the MIT License.
# SPDX-License-Identifier: MIT

# VITA - DIFI sender

# run python program DS (Difi Send Packet)

# Send Context
# Test A
python3 dcs.py --address 10.247.32.146 --port 4991
# Test B
python3 dcs.py --address 10.247.32.244 --port 4991
# Test W
python3 dcs.py --address 10.247.32.8 --port 4991

# Send Data
# Test A
python3 dds.py --address 10.247.32.146 --port 4991
# Test B
python3 dds.py --address 10.247.32.244 --port 4991
# Test W
python3 dds.py --address 10.247.32.8 --port 4991


# Send Version
# Test A
python3 dvs.py --address 10.247.32.146 --port 4991
# Test B
python3 dvs.py --address 10.247.32.244 --port 4991
# Test W
python3 dvs.py --address 10.247.32.8 --port 4991

