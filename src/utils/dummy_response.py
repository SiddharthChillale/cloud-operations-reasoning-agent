import asyncio
import json
from typing import AsyncGenerator

DUMMY_STEPS = [
    {
        "type": "planning",
        "step_type": "PlanningStep",
        "step_number": 1,
        "plan": "I need to process the user's request about EC2 instances. Let me first describe the architecture and then retrieve information about running instances.",
    },
    {
        "type": "action",
        "step_type": "ActionStep",
        "step_number": 2,
        "model_output": json.dumps(
            {
                "thought": "I need to list EC2 instances to provide accurate information. I'll use the describe_instances API to get details.",
                "code": "import boto3\n\n# Create EC2 client\n# This will be executed in the sandbox\nec2 = boto3.client('ec2', region_name='us-east-2')\n\n# Describe running instances\nresponse = ec2.describe_instances(\n    Filters=[\n        {'Name': 'instance-state-name', 'Values': ['running']}\n    ],\n    MaxResults=3\n)\n\n# Extract instance details\ninstances = []\nfor reservation in response.get('Reservations', []):\n    for instance in reservation.get('Instances', []):\n        instances.append({\n            'InstanceId': instance.get('InstanceId'),\n            'InstanceType': instance.get('InstanceType'),\n            'State': instance.get('State', {}).get('Name'),\n            'LaunchTime': str(instance.get('LaunchTime')),\n            'Tags': instance.get('Tags', [])\n        })\n\nprint(f\"Found {len(instances)} running instances\")\nprint(instances)",
            }
        ),
        "code_action": "import boto3\n\n# Create EC2 client\n# This will be executed in the sandbox\nec2 = boto3.client('ec2', region_name='us-east-2')\n\n# Describe running instances\nresponse = ec2.describe_instances(\n    Filters=[\n        {'Name': 'instance-state-name', 'Values': ['running']}\n    ],\n    MaxResults=3\n)\n\n# Extract instance details\ninstances = []\nfor reservation in response.get('Reservations', []):\n    for instance in reservation.get('Instances', []):\n        instances.append({\n            'InstanceId': instance.get('InstanceId'),\n            'InstanceType': instance.get('InstanceType'),\n            'State': instance.get('State', {}).get('Name'),\n            'LaunchTime': str(instance.get('LaunchTime')),\n            'Tags': instance.get('Tags', [])\n        })\n\nprint(f\"Found {len(instances)} running instances\")\nprint(instances)",
        "observations": "Found 3 running EC2 instances:\n- i-0abc123def456 (t3.medium, running)\n- i-0xyz789abc123 (t3.large, running)\n- i-0mno456pqr789 (t2.micro, running)",
        "error": None,
        "is_final_answer": False,
    },
    {
        "type": "action",
        "step_type": "ActionStep",
        "step_number": 3,
        "model_output": json.dumps(
            {
                "thought": "I have retrieved the EC2 instance information. Now I'll compile this into a comprehensive response for the user.",
                "code": "respond",
            }
        ),
        "code_action": "respond",
        "observations": "Compiling the response with instance details and pricing information.",
        "error": None,
        "is_final_answer": False,
    },
]

DUMMY_FINAL_OUTPUT = """## EC2 Instances Overview

I found **3 running EC2 instances** in the us-east-2 region:

### Instance Details

| Instance ID | Type | State | Launch Time |
|-------------|------|-------|--------------|
| i-0abc123def456 | t3.medium | running | 2024-01-15 10:30:00 |
| i-0xyz789abc123 | t3.large | running | 2024-01-20 14:45:00 |
| i-0mno456pqr789 | t2.micro | running | 2024-02-01 09:15:00 |

### Instance Information

1. **i-0abc123def456** (t3.medium)
   - vCPUs: 2
   - Memory: 4 GiB
   - Network: Up to 5 Gbps

2. **i-0xyz789abc123** (t3.large)
   - vCPUs: 2
   - Memory: 8 GiB
   - Network: Up to 10 Gbps

3. **i-0mno456pqr789** (t2.micro)
   - vCPUs: 1
   - Memory: 1 GiB
   - Network: Low to Moderate

---

*This is a **dummy response** for development purposes.*"""


async def generate_dummy_response(user_query: str) -> AsyncGenerator[str, None]:
    yield json.dumps({"type": "message", "role": "user", "content": user_query})

    await asyncio.sleep(1)

    for i, step in enumerate(DUMMY_STEPS):
        yield json.dumps(step)
        if i < len(DUMMY_STEPS) - 1:
            await asyncio.sleep(2)

    await asyncio.sleep(1)

    yield json.dumps(
        {
            "type": "final",
            "output": DUMMY_FINAL_OUTPUT,
            "output_type": "text",
            "url": None,
            "mime_type": None,
        }
    )
    await asyncio.sleep(5)
    yield json.dumps({"type": "done", "output": DUMMY_FINAL_OUTPUT})
